# Point Sellier - Inkscape Extension / Extension Inkscape

[🇫🇷 Version Française](#-français) | [🇬🇧 English Version](#-english)

---

## 🇫🇷 Français

### Description
**Point Sellier** est une extension pour **Inkscape** conçue pour faciliter la création de patrons (notamment en maroquinerie et travail du cuir). Elle permet de dupliquer et de répartir automatiquement des points de couture ou des motifs le long d'un chemin vectoriel, avec un contrôle précis sur la taille, l'espacement, les décalages, ainsi que des repères colorés adaptés à la découpe et au traçage laser.

### Fonctionnalités & Effets dans Inkscape

#### 1. Formes de points disponibles (`typePoint`)
L'extension vous permet d'orienter le point le long de votre ligne tracée :
* **Ligne dans l'axe** (`LigneH`) : Trace une ligne parallèle/tangente au chemin.
* **Ligne perpendiculaire** (`LigneV`) : Trace une ligne orthogonale au chemin (style griffe à frapper).
* **Cercle** (`Cercle`) : Place des perforations circulaires (pour poinçon ou emporte-pièce).
* **Ligne à 45° vers la droite** (`LigneG45`) : Orientée à 45° pour imiter la couture point sellier traditionnelle.
* **Ligne à 45° vers la gauche** (`LigneD45`) : Orientée à -45°.

#### 2. Modes d'espacement et calculs automatiques
* **Espacement fixe / Nombre fixe** : Vous définissez la taille du point, l'espace entre deux points et/ou le nombre total de points.
* **Calcul Auto de l'espace (`autoSpace`)** : Calcule automatiquement l'espacement idéal en fonction de la longueur de la ligne et du nombre de points souhaité.
* **Calcul Auto du nombre (`autoRepeat`)** : Rempli tout le chemin en calculant le nombre maximal de points possibles.
* **Calcul Auto du décalage (`autoOffset`)** : Centre automatiquement l'ensemble de la couture le long du chemin pour éviter que le premier ou le dernier point ne déborde des extrémités.

#### 3. Options avancées & Marquage laser
* **Marquage rythmique (`autoMark`)** : Génère un calque d'alignement supplémentaire avec des repères visuels de couleur différente :
  * *Tous les X points* (`markX`) : Ajoute une marque colorée tous les $N$ points (par défaut couleur `#ffaa00`).
  * *Par fraction* (`markFraction`) : Divise le chemin en fractions égales (1/2, 1/3, etc., par défaut couleur `#ff0000`).
* **Masquage du chemin initial (`autoMask`)** : Masque le tracé de référence et passe la couleur de la ligne en vert (`#00ff00`), ce qui est idéal pour différencier la ligne de coupe de la ligne de tracé pour le logiciel laser.
* **Texte d'information (`textInfos`)** : Affiche directement sous forme de texte sur votre canevas les détails du tracé (longueur, nombre de points, identifiant).

---

### Mise en Œuvre & Découpage Technique

* **Langage & Bibliothèques** : Écrit en **Python 3** avec l'API `inkex` d'Inkscape.
* **Transformation Vectorielle** : L'extension utilise la classe `Diffeo` et applique la technique de *linearization* (`CubicSuperPath`) pour discrétiser les courbes Bézier du chemin en segments droits et mapper précisément les motifs le long des tangente et normale de la courbe.
* **Compatibilité** : Testé sur **Inkscape 1.3+** (Linux / Windows / macOS).

### Installation

1. Téléchargez les deux fichiers du projet :
   * `ps_couture.py`
   * `ps_couture.inx`
2. Copiez ces deux fichiers dans votre dossier d'extensions utilisateur Inkscape :
   * **Linux** : `~/.config/inkscape/extensions/`
   * **Windows** : `%APPDATA%\inkscape\extensions\`
   * **macOS** : `~/Library/Application Support/org.inkscape.Inkscape/config/inkscape/extensions/`
3. Redémarrez Inkscape.
4. L'extension est accessible via le menu : `Extensions` > `Création patron cuir` > `Point sellier`.

---

## 🇬🇧 English

### Description
**Point Sellier** (Saddle Stitch) is an **Inkscape** extension created to streamline pattern design, specifically for leathercraft and stitch pattern layout. It automatically repeats and aligns stitch markers or geometry along any vector path with full control over sizing, spacing, offsets, and color-coded laser markings.

### Features & Effects in Inkscape

#### 1. Available Stitch Shapes (`typePoint`)
Align stitch geometry relative to the path tangent:
* **Axial line** (`LigneH`): Line parallel/tangent to the path.
* **Perpendicular line** (`LigneV`): Line orthogonal to the path (chisel punch style).
* **Circle** (`Cercle`): Circular holes (for round punches).
* **45° right-leaning line** (`LigneG45`): 45° angled line simulating traditional hand saddle stitching.
* **45° left-leaning line** (`LigneD45`): -45° angled line.

#### 2. Spacing & Automatic Calculations
* **Fixed Spacing / Count**: Set custom point size, gap distance, and total count.
* **Auto Spacing (`autoSpace`)**: Automatically computes equal spacing based on path length and required stitch count.
* **Auto Repeat (`autoRepeat`)**: Fills the entire path with maximum possible stitches given the spacing constraints.
* **Auto Offset (`autoOffset`)**: Automatically centers the stitches along the curve so start and end points remain balanced.

#### 3. Advanced Options & Laser Workflows
* **Pattern Marking (`autoMark`)**: Generates secondary color-coded alignment marks:
  * *Every X stitches* (`markX`): Adds a marker every $N$ stitches (default orange `#ffaa00`).
  * *By Fraction* (`markFraction`): Divides the path into equal fractional segments (1/2, 1/3, etc., default red `#ff0000`).
* **Hide original path (`autoMask`)**: Automatically hides the original guide path and sets its stroke to green (`#00ff00`), allowing easy separation between cut and score/stitch layers in laser software.
* **Text Info (`textInfos`)**: Appends textual metadata directly to the canvas (total path length, stitch count, unit).

---

### Technical Implementation

* **Language & API**: Built with **Python 3** using Inkscape's official `inkex` extension library.
* **Vector Transformation**: Extends `pathmodifier.Diffeo`. It converts Bézier components into linearized segment lists (`CubicSuperPath`) to calculate arc lengths and project pattern coordinates dynamically along curve tangents.
* **Compatibility**: Tested on **Inkscape 1.3+** (Linux / Windows / macOS).

### Installation

1. Download the extension files:
   * `ps_couture.py`
   * `ps_couture.inx`
2. Move both files into your Inkscape user extensions folder:
   * **Linux**: `~/.config/inkscape/extensions/`
   * **Windows**: `%APPDATA%\inkscape\extensions\`
   * **macOS**: `~/Library/Application Support/org.inkscape.Inkscape/config/inkscape/extensions/`
3. Restart Inkscape.
4. Access the tool via: `Extensions` > `Création patron cuir` > `Point sellier`.
