# Extensions Inkscape - Générateur Gcode Laser / Inkscape Extensions - Leathercraft & Laser G-Code

[🇫🇷 Version Française](#-français) | [🇬🇧 English Version](#-english)

---

<a name="français"></a>
## 🇫🇷 Français

### Description
Ce dépôt regroupe un ensemble de 3 extensions pour **Inkscape** dédiées à la fabrication numérique (découpe et gravure laser via G-Code) :

1. **Générateur Gcode pour Laser (`path2laser`)** : Convertit directement les chemins vectoriels Inkscape en fichier G-Code optimisé pour la gravure et la découpe laser (avec gestion dynamique des puissances/vitesses par couleur et réordonnancement intelligent).

---


### 1. Extension : Générateur Gcode pour Laser (`path2laser`)

#### Effets et Fonctionnalités dans Inkscape
* **Traitement selon la couleur des tracés (RGB + Alpha)** :
  * **Bleu pur (Canal Bleu ≥ 100)** = **Gravure**.
  * **Rouge pur (Canal Rouge ≥ 100)** = **Découpe**.
  * **Variation de vitesse** : La valeur du canal de couleur fait varier la vitesse de 10% à 100% de la vitesse paramétrée.
  * **Variation de puissance** : L’opacité du tracé (Canal Alpha / Stroke Opacity) fait varier la puissance du laser de 0% à 100%.
* **Gestion des passes et de l'axe Z** :
  * Découpe multi-passes paramétrable avec incrément de profondeur Z à chaque passe.
* **Remplissage par des hachures (`path2laser_fill`)** :
  * Remplissage par des hachures sur le chemin fermé qui contiennent un fond de couleur bleu.
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
   * `Extensions` ➔ `Générateur Gcode Laser` ➔ `Generateur Gcode pour laser a partir des chemins`

---

<a name="english"></a>
## 🇬🇧 English

### Description
This repository contains a suite of 3 **Inkscape** extensions dedicated to digital fabrication (laser cutting and engraving via G-Code):

1. **Laser Gcode Generator (`path2laser`)**: Converts Inkscape vector paths into optimized G-Code files for laser cutters and engravers (featuring color-driven speed/power controls and smart reordering).

---

### 1. Extension: Laser G-Code Generator (`path2laser`)

#### Features & Effects in Inkscape
* **Color-Coded Operation Control (RGB + Alpha)**:
  * **Pure Blue (Blue Channel ≥ 100)** = **Engraving**.
  * **Pure Red (Red Channel ≥ 100)** = **Laser Cutting**.
  * **Speed Modulation**: Color channel value adjusts speed dynamically between 10% and 100% of base speed.
  * **Power Modulation**: Stroke Opacity (Alpha Channel) scales laser power output from 0% to 100%.
* **Multi-pass & Z-Axis Control**:
  * Configurable cutting passes with step-down Z-depth increments per pass.
* **Filling with hatching (`path2laser_fill`)**:
  * Filling with hatching on blue background closed path.
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
   * `Extensions` ➔ `Générateur Gcode Laser` ➔ `Generateur Gcode pour laser a partir des chemins`
