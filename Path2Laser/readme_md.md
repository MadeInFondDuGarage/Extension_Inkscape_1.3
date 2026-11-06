# Extensions Inkscape - Création Patron Cuir & Générateur Gcode Laser / Inkscape Extensions - Leathercraft & Laser G-Code

[🇫🇷 Version Française](#-français) | [🇬🇧 English Version](#-english)

---

<a name="français"></a>
## 🇫🇷 Français

### Description
Ce dépôt regroupe un ensemble de 3 extensions pour **Inkscape** dédiées à la création de patrons de maroquinerie / travail du cuir et à la fabrication numérique (découpe et gravure laser via G-Code) :

1. **Point Sellier (`ps_couture`)** : Génère automatiquement des motifs de coutures vectoriels (points sellier) le long d'un chemin.
2. **Gabarit (`ps_gabarit`)** : Permet d'insérer des repères de positionnement (cercles/carrés aux nœuds) ou de créer des lignes de décalage (offset intérieur/extérieur) pour tracer la ligne de couture par rapport au bord.
3. **Générateur Gcode pour Laser (`path2laser`)** : Convertit directement les chemins vectoriels Inkscape en fichier G-Code optimisé pour la gravure et la découpe laser (avec gestion dynamique des puissances/vitesses par couleur et réordonnancement intelligent).

---

### 1. Extension : Point Sellier (`ps_couture`)

#### Effets et Fonctionnalités dans Inkscape
* **Types de points configurables (`typePoint`)** :
  * `LigneH` : Ligne dans l'axe (parallèle/tangente au chemin).
  * `LigneV` : Ligne perpendiculaire au chemin (style griffe à frapper).
  * `Cercle` : Repère circulaire (trous circulaires pour poinçon ou emporte-pièce).
  * `LigneG45` / `LigneD45` : Lignes inclinées à 45° (droite ou gauche) simulant le perçage à la griffe à frapper ou le point sellier traditionnel.
* **Calculs Automatiques** :
  * Espacement auto (`autoSpace`) ou répétition auto (`autoRepeat`).
  * Décalage du 1er point auto (`autoOffset`) pour centrer parfaitement la rangée de points le long du chemin.
* **Marquage & Options Laser** :
  * **Masquage du chemin initial** (`autoMask`) : Masque le tracé de base et lui applique une couleur verte (`#00ff00`) compatible avec l'isolation des lignes de découpe/gravure laser.
  * **Marquage coloré rythmique** (`autoMark`) : Ajoute des repères visuels (tous les X points ou par fraction 1/N) de couleurs différentes (rouge `#ff0000` ou orange `#ffaa00`).
  * **Informations textuelles** (`textInfos`) : Affiche le nombre de points et la longueur totale directement sur le document.

#### Mise en œuvre technique
L'extension hérite de `pathmodifier.Diffeo`. Elle linéarise la courbe Bézier d'origine (`linearize`), effectue les calculs géométriques de mise à l'échelle/espacement, puis applique une transformation d'espace (`applyDiffeo`) pour orienter et plaquer chaque motif de point le long des tangentes et normales de la courbe.

---

### 2. Extension : Gabarit (`ps_gabarit`)

#### Effets et Fonctionnalités dans Inkscape
* **Repères aux nœuds (Gabarit ponctuel)** :
  * Place des **Cercles** ou des **Carrés** configurables en taille sur chaque nœud (point de contrôle) d'un chemin.
* **Décalage de contour (Offset dynamique)** :
  * **Décalage in** (`Interieur`) / **Décalage out** (`Exterieur`) : Génère un nouveau tracé parallèle (en vert `#00ff00`) à une distance paramétrable en mm, pouces ou pixels.

#### Mise en œuvre technique
Pour les formes géométriques (cercles/carrés), l'extension parcourt les `end_points` des segments Bézier transformés et insère des objets `inkex.Circle` ou `inkex.Rectangle`. Pour les décalages, elle analyse la direction du chemin (`csp_subpath_ccw`), ajuste l'orientation des points de contrôle Bézier avec un solveur cubique (`cubic_solver`, `csp_true_bounds`), et crée un élément SVG nativement interprété par Inkscape comme `inkscape:offset` (`sodipodi:type="inkscape:offset"`).

---

### 3. Extension : Générateur Gcode pour Laser (`path2laser`)

#### Effets et Fonctionnalités dans Inkscape
* **Traitement selon la couleur des tracés (RGB + Alpha)** :
  * **Bleu pur (Canal Bleu ≥ 100)** = **Gravure**.
  * **Rouge pur (Canal Rouge ≥ 100)** = **Découpe**.
  * **Variation de vitesse** : La valeur du canal de couleur fait varier la vitesse de 10% à 100% de la vitesse paramétrée.
  * **Variation de puissance** : L’opacité du tracé (Canal Alpha / Stroke Opacity) fait varier la puissance du laser de 0% à 100%.
* **Gestion des passes et de l'axe Z** :
  * Découpe multi-passes paramétrable avec incrément de profondeur Z à chaque passe.
* **Réordonnancement intelligent (`path2laser_order`)** :
  * Réordonne les calques et objets dans l'ordre optimal de fabrication : **Gravures (Bleu) d'abord**, puis **Découpes (Rouge) ensuite**.
* **Prévisualisation & Export** :
  * Génère un groupe visuel de prévisualisation dans Inkscape (lignes d'usinage et arcs bi-arc).
  * Exporte un fichier `.gcode` compatible avec **bCNC**, Marlin ou GRBL.

#### Mise en œuvre technique
L'extension parcourt l'arbre XML SVG (`inkex.EffectExtension`). Elle utilise un algorithme d'interpolation bi-arc (`biarc`) pour convertir les courbes Bézier complexes en segments linéaires (`G1`) et arcs de cercle (`G2`/`G3`) pris en charge par les contrôleurs CNC/Laser. Le module `path2laser_order.py` modifie la structure XML sans altérer la hiérarchie des groupes pour garantir l'exécution séquentielle gravure ➔ découpe.

---

### Installation

1. Copiez l'ensemble des fichiers (`ps_couture.py`, `ps_couture.inx`, `ps_gabarit.py`, `ps_gabarit.inx`, `path2laser_gcode.py`, `path2laser_order.py`, `path2laser_gcode.inx`) dans votre dossier d'extensions utilisateur Inkscape :
   * **Linux** : `~/.config/inkscape/extensions/`
   * **macOS** : `~/Library/Application Support/org.inkscape.Inkscape/config/inkscape/extensions/`
   * **Windows** : `%APPDATA%\inkscape\extensions\`
2. Redémarrez Inkscape.
3. Retrouvez les outils dans le menu :
   * `Extensions` ➔ `Création patron cuir` ➔ `Point sellier`
   * `Extensions` ➔ `Création patron cuir` ➔ `Gabarit`
   * `Extensions` ➔ `Générateur Gcode Laser` ➔ `Generateur Gcode pour laser a partir des chemins`

---

<a name="english"></a>
## 🇬🇧 English

### Description
This repository contains a suite of 3 **Inkscape** extensions dedicated to leathercraft pattern design and digital fabrication (laser cutting and engraving via G-Code):

1. **Point Sellier / Saddle Stitch (`ps_couture`)**: Automatically generates vector stitch marks (saddle stitching) along any curved or straight path.
2. **Gabarit / Template (`ps_gabarit`)**: Adds positioning markers (circles/squares at nodes) or creates dynamic offset lines (inner/outer spacing) to establish stitch alignment lines.
3. **Laser Gcode Generator (`path2laser`)**: Converts Inkscape vector paths into optimized G-Code files for laser cutters and engravers (featuring color-driven speed/power controls and smart reordering).

---

### 1. Extension: Saddle Stitch (`ps_couture`)

#### Features & Effects in Inkscape
* **Configurable Stitch Patterns (`typePoint`)**:
  * `LigneH`: Axial line (parallel/tangent to path).
  * `LigneV`: Perpendicular line (pricking iron / chisel style).
  * `Cercle`: Circular hole/dot (punched holes).
  * `LigneG45` / `LigneD45`: 45° angled lines (right or left) simulating traditional hand saddle stitching.
* **Smart Automations**:
  * Auto spacing (`autoSpace`) or auto count (`autoRepeat`).
  * Auto offset (`autoOffset`) to perfectly center stitches along the curve.
* **Marking & Laser Features**:
  * **Path Masking** (`autoMask`): Hides the original path and sets it to green (`#00ff00`) for laser line management.
  * **Rhythmic Marking** (`autoMark`): Generates color-coded marks (every X stitches or by fraction 1/N) in red (`#ff0000`) or orange (`#ffaa00`).
  * **Text Information** (`textInfos`): Prints total stitch count and path length directly onto the canvas.

#### Technical Implementation
Built upon `pathmodifier.Diffeo`. It linearizes the source Bézier curve (`linearize`), computes spatial intervals, and applies a transformation kernel (`applyDiffeo`) to map and align each custom stitch element to the curve's tangents and normals.

---

### 2. Extension: Template / Gabarit (`ps_gabarit`)

#### Features & Effects in Inkscape
* **Node Markers (Point Templates)**:
  * Places size-adjustable **Circles** or **Squares** on node endpoints.
* **Path Offsets (Dynamic Outline Spacing)**:
  * **Inner Offset** (`Interieur`) / **Outer Offset** (`Exterieur`): Creates a parallel vector path (green `#00ff00`) at a user-defined distance (mm, inches, px).

#### Technical Implementation
For node shapes, it extracts `end_points` from transformed paths and appends `inkex.Circle` or `inkex.Rectangle` nodes. For contour offsets, it assesses path direction (`csp_subpath_ccw`), solves cubic Bézier equations (`cubic_solver`, `csp_true_bounds`), and generates a native SVG `inkscape:offset` element (`sodipodi:type="inkscape:offset"`).

---

### 3. Extension: Laser G-Code Generator (`path2laser`)

#### Features & Effects in Inkscape
* **Color-Coded Operation Control (RGB + Alpha)**:
  * **Pure Blue (Blue Channel ≥ 100)** = **Engraving**.
  * **Pure Red (Red Channel ≥ 100)** = **Laser Cutting**.
  * **Speed Modulation**: Color channel value adjusts speed dynamically between 10% and 100% of base speed.
  * **Power Modulation**: Stroke Opacity (Alpha Channel) scales laser power output from 0% to 100%.
* **Multi-pass & Z-Axis Control**:
  * Configurable cutting passes with step-down Z-depth increments per pass.
* **Smart Order Optimization (`path2laser_order`)**:
  * Automatically reorganizes layers and elements so that **Engravings (Blue) execute first**, followed by **Cuts (Red)**.
* **Preview & Export**:
  * Draws in-canvas bi-arc preview paths in Inkscape.
  * Exports clean `.gcode` output tailored for **bCNC**, Marlin, or GRBL firmware.

#### Technical Implementation
Parses the document structure using `inkex.EffectExtension`. Employs bi-arc approximation algorithms (`biarc`) to convert complex Bézier paths into G01 linear moves and G02/G03 arc commands. The accompanying `path2laser_order.py` script reorders XML nodes within their parent groups to enforce the Engrave-then-Cut pipeline.

---

### Installation Guide

1. Copy all script files (`ps_couture.py`, `ps_couture.inx`, `ps_gabarit.py`, `ps_gabarit.inx`, `path2laser_gcode.py`, `path2laser_order.py`, `path2laser_gcode.inx`) into your Inkscape extensions directory:
   * **Linux**: `~/.config/inkscape/extensions/`
   * **macOS**: `~/Library/Application Support/org.inkscape.Inkscape/config/inkscape/extensions/`
   * **Windows**: `%APPDATA%\inkscape\extensions\`
2. Restart Inkscape.
3. Access the extensions from the menu:
   * `Extensions` ➔ `Création patron cuir` ➔ `Point sellier`
   * `Extensions` ➔ `Création patron cuir` ➔ `Gabarit`
   * `Extensions` ➔ `Générateur Gcode Laser` ➔ `Generateur Gcode pour laser a partir des chemins`