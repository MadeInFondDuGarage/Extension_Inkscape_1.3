# Outils Patron Cuir - Extensions Inkscape / Leathercraft Tools - Inkscape Extensions

[🇫🇷 Version Française](#-français) | [🇬🇧 English Version](#-english)

---

## 🇫🇷 Français

### Description
Ce dépôt regroupe deux extensions pour **Inkscape** conçues pour faciliter la création et la préparation de patrons (notamment pour la maroquinerie et le travail du cuir) :
1. **Point Sellier** (`ps_couture.py`) : Permet de générer et répartir des points de couture ou perforations le long de tracés vectoriels.
2. **Gabarit** (`ps_gabarit.py`) : Permet d'ajouter des repères géométriques sur les nœuds ou de créer des lignes de décalage (offset dynamique) pour positionner les lignes de couture.

---

### 1. Extension : Point Sellier

#### Effets & Fonctionnalités
* **Types de points (`typePoint`)** :
  * *Ligne dans l'axe* (`LigneH`) : Ligne parallèle/tangente au chemin.
  * *Ligne perpendiculaire* (`LigneV`) : Ligne orthogonale (style griffe à frapper).
  * *Cercle* (`Cercle`) : Trous circulaires pour poinçon ou emporte-pièce.
  * *Ligne à 45° vers la droite / gauche* (`LigneG45` / `LigneD45`) : Orientation inclinée simulant le point sellier traditionnel.
* **Modes d'espacement et automatisations** :
  * *Calcul Auto de l'espace (`autoSpace`)* : Ajuste l'intervalle entre les points pour un nombre défini de répétitions.
  * *Calcul Auto du nombre (`autoRepeat`)* : Remplit tout le chemin en fonction de l'espacement configuré.
  * *Calcul Auto du décalage (`autoOffset`)* : Centre automatiquement la rangée de points le long de la ligne.
* **Options avancées & Marquage laser** :
  * *Marquage rythmique (`autoMark`)* : Ajoute des repères colorés (tous les X points ou par fraction de ligne).
  * *Masquage du chemin initial (`autoMask`)* : Masque le chemin de référence et passe sa couleur en vert (`#00ff00`) pour isoler les lignes de tracé/découpe laser.
  * *Texte d'information (`textInfos`)* : Affiche les métadonnées (longueur, nombre de points) sur le canevas.

---

### 2. Extension : Gabarit

#### Effets & Fonctionnalités
* **Styles de gabarit (`stylegab`)** :
  * *Cercle* : Place des cercles de diamètre défini sur chaque nœud (point de contrôle) du chemin.
  * *Carré* : Place des carrés centrés sur chaque nœud du chemin.
  * *Décalage in (`Interieur`)* : Génère un décalage interne (offset dynamique Inkscape) de la forme sélectionnée à une distance précise.
  * *Décalage out (`Exterieur`)* : Génère un décalage externe de la forme sélectionnée.
* **Mise en forme** : Tous les éléments de gabarit générés sont automatiquement colorés en vert (`#00ff00`) avec une épaisseur fine (`0.2mm`), optimisés pour la lecture par logiciel de découpe/gravure laser.

---

### Mise en Œuvre & Découpage Technique

* **Langage & API** : Développé en **Python 3** avec la bibliothèque officielle `inkex` d'Inkscape.
* **Moteur Mathématique & Transformations** :
  * `ps_couture.py` s'appuie sur l'interpolation Bézier et la discrétisation `CubicSuperPath` pour mapper précisément des motifs 2D le long des normales et tangentes du chemin original.
  * `ps_gabarit.py` résout les équations cubiques (`cubic_solver`), détermine l'orientation horaire/anti-horaire (`csp_subpath_ccw`) et injecte un élément SVG `inkscape:offset` dynamique lié à la forme d'origine.
* **Compatibilité** : Inkscape 1.3+ (Linux, Windows, macOS).

---

### Installation

1. Téléchargez tous les fichiers du projet (`.py` et `.inx`) :
   * `ps_couture.py` & `ps_couture.inx`
   * `ps_gabarit.py` & `ps_gabarit.inx`
2. Copiez l'ensemble des fichiers dans le dossier d'extensions d'Inkscape :
   * **Linux** : `~/.config/inkscape/extensions/`
   * **Windows** : `%APPDATA%\inkscape\extensions\`
   * **macOS** : `~/Library/Application Support/org.inkscape.Inkscape/config/inkscape/extensions/`
3. Redémarrez Inkscape. Les deux extensions sont accessibles dans le menu :
   * `Extensions` > `Création patron cuir` > `Point sellier`
   * `Extensions` > `Création patron cuir` > `Gabarit`

---
---

## 🇬🇧 English

### Description
This repository contains two **Inkscape** extensions designed for leathercraft pattern design and vector drafting:
1. **Point Sellier** (`ps_couture.py`): Generates and distributes stitching holes or custom marks along vector paths.
2. **Gabarit** (`ps_gabarit.py`): Creates node-based reference markers (circles/squares) or dynamic outline offsets to set up stitching margins.

---

### 1. Extension: Point Sellier (Saddle Stitch)

#### Features & Effects
* **Stitch Types (`typePoint`)**:
  * *Axial line* (`LigneH`): Line parallel/tangent to the path.
  * *Perpendicular line* (`LigneV`): Orthogonal line (chisel punch style).
  * *Circle* (`Cercle`): Round holes (for punches/punched holes).
  * *45° Right / Left line* (`LigneG45` / `LigneD45`): Angled lines simulating traditional hand saddle stitching.
* **Spacing Modes & Automation**:
  * *Auto Space (`autoSpace`)*: Automatically computes uniform gap distance based on the given stitch count.
  * *Auto Repeat (`autoRepeat`)*: Fills the entire path according to defined spacing.
  * *Auto Offset (`autoOffset`)*: Centers the stitch row along the path to maintain balanced margins at start and end.
* **Advanced Options & Laser Tools**:
  * *Rhythmic Marking (`autoMark`)*: Adds color-coded visual guide marks (every X stitches or fractional intervals).
  * *Hide Original Path (`autoMask`)*: Automatically hides the guide path and changes its stroke to green (`#00ff00`) for easy laser cutter layer management.
  * *Text Information (`textInfos`)*: Outputs path length and stitch count directly onto the canvas.

---

### 2. Extension: Gabarit (Pattern Margin Guide)

#### Features & Effects
* **Guide Styles (`stylegab`)**:
  * *Circle*: Places circles of a specified radius at each path node.
  * *Square*: Places centered squares at each path node.
  * *Offset in (`Interieur`)*: Generates an inward dynamic offset path at a set distance.
  * *Offset out (`Exterieur`)*: Generates an outward dynamic offset path at a set distance.
* **Styling**: Generated guide elements are automatically assigned a thin green stroke (`#00ff00`, `0.2mm`), optimized for laser scoring and drafting software.

---

### Technical Implementation

* **Language & Core API**: Built with **Python 3** using Inkscape's `inkex` extension core.
* **Vector Mathematics**:
  * `ps_couture.py` uses Bézier segment linearization (`CubicSuperPath`) to project stitch geometries along path tangents and normals.
  * `ps_gabarit.py` solves cubic Bézier equations (`cubic_solver`), calculates path winding order (`csp_subpath_ccw`), and injects dynamic `inkscape:offset` SVG elements linked to the original path.
* **Compatibility**: Inkscape 1.3+ (Linux, Windows, macOS).

### Installation

1. Download all repository files (`.py` and `.inx`):
   * `ps_couture.py` & `ps_couture.inx`
   * `ps_gabarit.py` & `ps_gabarit.inx`
2. Copy the files into your Inkscape extensions folder:
   * **Linux**: `~/.config/inkscape/extensions/`
   * **Windows**: `%APPDATA%\inkscape\extensions\`
   * **macOS**: `~/Library/Application Support/org.inkscape.Inkscape/config/inkscape/extensions/`
3. Restart Inkscape. Access both tools under:
   * `Extensions` > `Création patron cuir` > `Point sellier`
   * `Extensions` > `Création patron cuir` > `Gabarit`
