# Generateur Gcode Laser Mode Raster - Inkscape Extension / Extension Inkscape

[🇫🇷 Version Française](#-français) | [🇬🇧 English Version](#-english)

## 🇫🇷 Français

### Description

**Generateur Gcode Laser Mode Raster (`raster2laser`)** est une extension pour **Inkscape** permettant de transformer n'importe quelle image ou dessin vectoriel (y compris les images matricielles et dégradés) en G-Code de gravure laser en mode ligne par ligne (*raster*). Spécialement optimisée pour être compatible avec **bCNC**, **GRBL** et **Marlin**, elle convertit les formes ou images du document en valeurs de puissance et mouvements horizontaux fluides pour la gravure laser.

### Fonctionnalités et Effets

* **Gestion des Résolutions et Export Image** :
  * **Taille du faisceau / Résolution** (`resolution`) : Ajuste le pas de balayage laser (1 mm, 0.5 mm, 0.2 mm, 0.1 mm) correspondant au diamètre du point focal.
  * **Remplacement de la transparence** (`bg_color`) : Remplace le fond transparent par du blanc (`#ffffff`) ou du noir (`#000000`).

* **Conversion Niveaux de Gris & Noir/Blanc** :
  * **Méthodes de conversion en niveaux de gris** (`grayscale_type`) : Formule pondérée RVB (`0.21R + 0.71G + 0.07B`), moyenne (`(R+G+B)/3`), canaux séparés (R, V ou B), ou extraction des couleurs Max/Min.
  * **Modes de binarisation** (`conversion_type`) : 
    * Seuil fixe Noir & Blanc (`BW_threshold`).
    * Seuil aléatoire (*Dithering / Trame aléatoire*).
    * Niveaux de gris continus (gravure variable).

* **Contrôle Laser et Machine** :
  * **Vitesse et Puissance** (`speed_ON` & `Power_ON`) : Définit la vitesse d'usinage en mm/min et la plage de puissance du laser (ex: S0 à S3000 ou S255).
  * **Inversion de l'axe Y** (`flip_y`) : Permet de basculer entre coordonnées informatiques et cartésiennes.
  * **Homing / Origine** (`homing`) : Choix du retour à l'origine en fin de gravure (`G28`, `G0 X0Y0Z0` ou Aucun).
  * **Délai d'allumage** (`power-delay`) : Ajoute une instruction de temporisation (`G4 Px.x`) avant la gravure.
  * **Mode Prévisualisation seule** (`preview_only`) : Génère uniquement l'image convertie sans créer le fichier G-Code final.

### Fonctionnement Technique

1. **Export PNG dynamique** : L'extension utilise l'interface en ligne de commande d'Inkscape (`inkex.command.inkscape`) pour exporter le document ou la sélection courante au format PNG avec la résolution (DPI) calculée d'après le diamètre du faisceau laser.
2. **Décodeur PNG natif Python** : L'image exportée est lue et décodée pixel par pixel via une implémentation pure Python de découpage de Chunks PNG (`Reader`, `decompress`, `undo_filter`).
3. **Traitement matriciel** : Une matrice d'intensité 2D est générée (`matrice[y][x]`). Chaque pixel est converti en valeur de gris (0 à 255) puis ajusté selon l'algorithme choisi (seuil fixe, aléatoire ou échelle linéaire).
4. **Génération G-Code optimisée** : Le parcours s'effectue ligne par ligne. Pour optimiser le temps d'usinage et la taille du fichier G-Code, l'extension regroupe les pixels adjacents de même intensité en une seule commande de déplacement (`G0`/`G1` avec commande de puissance `S#` proportionnelle).

### Installation

1. Copiez les fichiers `raster2laser_gcode.py` et `raster2laser.inx` (ou le fichier `.inx` correspondant) dans votre dossier d'extensions Inkscape :
   * **Linux** : `~/.config/inkscape/extensions/`
   * **macOS** : `~/Library/Application Support/org.inkscape.Inkscape/config/inkscape/extensions/`
   * **Windows** : `%APPDATA%\inkscape\extensions\`

2. Redémarrez Inkscape.

3. Retrouvez l'extension dans le menu : `Extensions` ➔ `Générateur Gcode Laser` ➔ `Générateur Gcode Laser mode Raster`.

---

## 🇬🇧 English

### Description

**Laser GCode Generator Raster Mode (`raster2laser`)** is an **Inkscape** extension designed to convert vector graphics, bitmaps, or shaded illustrations into line-by-line raster laser engraving G-Code. Tailored for compatibility with **bCNC**, **GRBL**, and **Marlin** firmware, it translates canvas elements into variable laser power outputs and smooth horizontal scanning movements.

### Features & Effects

* **Resolution and Export Settings**:
  * **Laser Spot Resolution** (`resolution`): Selects line-spacing step (1 mm, 0.5 mm, 0.2 mm, 0.1 mm) matching the laser beam spot size.
  * **Background Transparency Handling** (`bg_color`): Replaces transparent backgrounds with solid White (`#ffffff`) or Black (`#000000`).

* **Grayscale & B/W Conversion Modes**:
  * **Grayscale Conversion Formulas** (`grayscale_type`): Luma weighted (`0.21R + 0.71G + 0.07B`), Average (`(R+G+B)/3`), Single channels (Red, Green, Blue), or Max/Min color values.
  * **Thresholding Algorithms** (`conversion_type`): 
    * Fixed Black & White threshold (`BW_threshold`).
    * Random dithering threshold.
    * Continuous Grayscale engraving.

* **Laser & CNC Machine Controls**:
  * **Speed and Power** (`speed_ON` & `Power_ON`): Configures feed rate (mm/min) and max laser power scale (e.g. S0 to S3000 or S255).
  * **Y-Axis Inversion** (`flip_y`): Flips image vertically between screen coordinates and Cartesian coordinate space.
  * **Homing Routines** (`homing`): Post-engraving homing options (`G28`, `G0 X0Y0Z0`, or No Homing).
  * **Power-On Delay** (`power-delay`): Injects dwell commands (`G4 Px.x`) prior to firing the laser beam.
  * **Preview Mode** (`preview_only`): Renders converted processed bitmap preview without outputting G-Code files.

### Technical Implementation

1. **Dynamic PNG Export**: Invokes Inkscape's internal CLI command (`inkex.command.inkscape`) to rasterize the document or selected items into PNG format at calculated DPI values matching the specified beam diameter.
2. **Native Python PNG Decoder**: Reads PNG pixels using a pure Python chunk parser and decompressor (`Reader`, `decompress`, `undo_filter`).
3. **Pixel Matrix Processing**: Constructs a 2D intensity array (`matrice[y][x]`). Each pixel is processed into a 0–255 grayscale value and filtered using the selected threshold algorithm.
4. **Optimized G-Code Construction**: Traverses pixels scanline by scanline. To shrink file size and eliminate unnecessary machine stutter, contiguous pixels of identical intensity are combined into single linear movement blocks (`G0`/`G1` with scaled `S#` power arguments).

### Installation Guide

1. Copy `raster2laser_gcode.py` and `raster2laser.inx` (or your corresponding `.inx` file) into your Inkscape extensions folder:
   * **Linux**: `~/.config/inkscape/extensions/`
   * **macOS**: `~/Library/Application Support/org.inkscape.Inkscape/config/inkscape/extensions/`
   * **Windows**: `%APPDATA%\inkscape\extensions\`

2. Restart Inkscape.

3. Access the extension via menu: `Extensions` ➔ `Generateur Gcode Laser` ➔ `Generateur Gcode Laser mode Raster`.