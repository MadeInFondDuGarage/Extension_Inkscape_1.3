# Hatch Fill - Inkscape Extension / Extension Inkscape

[🇫🇷 Version Française](#-français) | [🇬🇧 English Version](#-english)

---

<a name="français"></a>
## 🇫🇷 Français

### Description
**Hatch Fill** est une extension pour **Inkscape** permettant de remplir des formes fermées (polygones, cercles, chemins vectoriels) et avec une couleur de emplissage (ne marche as sur des forme non remplie) par un tracé répétitif de lignes parallèles (hachures). Spécialement conçue pour le tracé mécanique (*plotting*), la gravure CNC et le dessin automatisé (type EggBot ou AxiDraw), elle permet d'optimiser les mouvements de l'outil et de simuler un remplissage de couleur avec des stylos ou gravures.

### Fonctionnalités et Effets
* **Réglages du motif de hachures** :
  * **Espacement** (`hatchSpacing`) : Définit la distance entre les lignes de hachure (en mm, cm, in, px, pt).
  * **Angle** (`hatchAngle`) : Oriente le réseau de hachures par rapport à l'horizontale (-360° à 360°).
  * **Hachures croisées** (`crossHatch`) : Applique une seconde passe de hachures perpendiculaire à la première.
* **Optimisation pour le tracé (*Plotting*)** :
  * **Connexion des extrémités** (`reducePenLifts`) : Réduit au maximum les levées de stylo/outil en raccordant les extrémités de hachures voisines par des courbes de Bézier fluides.
  * **Portée des raccordements** (`hatchScope`) : Plage de recherche (en multiples de la largeur de hachure) pour lier les segments.
* **Marges de sécurité & Précision** :
  * **Distance de sécurité / Enset** (`holdBackHatchFromEdges` & `holdBackSteps`) : Maintient les extrémités des hachures à une certaine distance des bords pour éviter de dépasser du tracé d'origine lors de l'utilisation de feutres/stylos.
  * **Tolérance** (`tolerance`) : Ajuste la précision de décomposition des courbes d'origine.

### Fonctionnement Technique
1. **Décomposition vectorielle** : L'extension convertit les objets SVG (`path`, `rect`, `circle`, `ellipse`, `polygon`, etc.) en sous-chemins Bézier simplifiés et identifie les contours fermés (`addPathVertices`).
2. **Calcul des intersections (Règle Pair/Impair)** : Un réseau de droites virtuelles est projeté à travers la boîte englobante de l'objet (`makeHatchGrid`). Pour chaque ligne, l'extension calcule les points d'intersection avec les segments du polygone (`intersect` / `interstices`). Un tri pair/impair détermine précisément les segments situés à l'intérieur de la forme.
3. **Inversion des transformations SVG** : L'extension conserve la matrice de transformation (`Transform`) des éléments pour appliquer l'inverse (`inverse_parent_transform`) sur le chemin de hachure généré, garantissant un alignement parfait au sein du groupe d'origine.
4. **Optimisation des leviers d'outil** : Lorsque l'option `reducePenLifts` est activée, un algorithme récursif (`recursivelyAppendNearbySegments`) relie les lignes adjacentes par des arcs Bézier cubic contrôlés (`BEZIER_OVERSHOOT_MULTIPLIER`) afin de garantir la continuité du tracé.

### Installation
1. Copiez les fichiers `hatch_fill.py` et `hatch_fill.inx` dans votre dossier d'extensions Inkscape :
   * **Linux** : `~/.config/inkscape/extensions/`
   * **macOS** : `~/Library/Application Support/org.inkscape.Inkscape/config/inkscape/extensions/`
   * **Windows** : `%APPDATA%\inkscape\extensions\`
2. Redémarrez Inkscape.
3. Retrouvez l'extension dans le menu : `Extensions` ➔ `Générer à partir du chemin` ➔ `Hatch fill`.

---

<a name="english"></a>
## 🇬🇧 English

### Description
**Hatch Fill** is an **Inkscape** extension designed to fill closed shapes (polygons, circles, vector paths) with back-and-forth line patterns (hatching). Optimized for pen plotters, CNC engraving, and automated drawing machines (such as EggBot or AxiDraw), it converts flat color fills into physical toolpath strokes with pen-lift minimization algorithms.

### Features & Effects
* **Hatch Pattern Controls**:
  * **Spacing** (`hatchSpacing`): Distance between hatch lines (in mm, cm, in, px, pt).
  * **Angle** (`hatchAngle`): Orientation of hatch lines relative to horizontal (-360° to 360°).
  * **Crosshatch** (`crossHatch`): Generates a secondary set of hatch lines perpendicular to the first.
* **Plotter & Pen Optimization**:
  * **Connect nearby ends** (`reducePenLifts`): Reduces pen lifts by joining adjacent hatch ends with smooth cubic Bézier curves.
  * **Range of end connections** (`hatchScope`): Sets the search radius (in multiples of hatch spacing) to join segments.
* **Safety & Precision Settings**:
  * **Safety distance** (`holdBackHatchFromEdges` & `holdBackSteps`): Holds back hatch line ends from the object's outer boundary to prevent ink bleeding over lines.
  * **Tolerance** (`tolerance`): Controls curve approximation accuracy for path decomposition.

### Technical Implementation
1. **Path Decomposition**: The script converts supported SVG nodes (`path`, `rect`, `circle`, `ellipse`, `polygon`, etc.) into simplified Bézier vertex arrays, retaining closed polygons (`addPathVertices`).
2. **Intersection Engine (Odd/Even Rule)**: Virtual hatch lines are projected across the bounding box (`makeHatchGrid`). Intersections with polygon edges are detected (`intersect` / `interstices`), sorted, and evaluated using an odd/even parity test to determine interior fill line segments.
3. **Transform Matrix Inversion**: The element's global SVG transformation matrix (`Transform`) is stored and inverted (`inverse_parent_transform`) when attaching the newly generated hatch path, preserving scale and positioning within the parent group.
4. **Pen-Lift Reduction Algorithm**: When enabled (`reducePenLifts`), a recursive path-joining algorithm (`recursivelyAppendNearbySegments`) connects neighboring hatch endpoints using cubic Bézier tangents (`BEZIER_OVERSHOOT_MULTIPLIER`), creating continuous toolpaths inside boundaries.

### Installation Guide
1. Copy `hatch_fill.py` and `hatch_fill.inx` into your Inkscape extensions folder:
   * **Linux**: `~/.config/inkscape/extensions/`
   * **macOS**: `~/Library/Application Support/org.inkscape.Inkscape/config/inkscape/extensions/`
   * **Windows**: `%APPDATA%\inkscape\extensions\`
2. Restart Inkscape.
3. Access the tool via menu: `Extensions` ➔ `Generate from Path` ➔ `Hatch fill`.
