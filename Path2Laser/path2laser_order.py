#!/usr/bin/env python
# coding=utf-8

################################################################################
#
# Ordonnancement des calques/groupes et des chemins pour path2laser_gcode
#
# Module appelé par path2laser_gcode.py, il travaille uniquement sur le document Inkscape.
#
# Ordre du gcode : path2laser_gcode lit chaque conteneur de la fin vers le début du XML,
# donc du plus en avant plan au plus en arrière plan dans Inkscape.
# Le début du gcode est donc l'élément le plus en avant plan.
#
# Règles (seuls les calques/groupes visibles et les chemins visibles de couleur reconnue sont traités) :
#   - calque/groupe de gravure seule   : en premier dans le gcode
#   - calque/groupe de découpe seule   : ensuite
#   - calque/groupe qui mélange les 2  : en dernier dans le gcode (le plus en arrière plan dans Inkscape)
#   - dans un calque/groupe qui mélange : les chemins de gravure puis ceux de découpe
# Les autres éléments (invisibles, couleur non reconnue, orientation, aperçu...) gardent leur place.
# Le réordonnancement se fait entre éléments de même parent, la hiérarchie n'est jamais modifiée.
#
################################################################################
from inkex import Group, PathElement

ATTR_IGNORE = "Path2Laser"  # attribut des groupes créés par l'extension (orientation, aperçu)
RANG = {"grav": 0, "cut": 1}  # ordre dans le gcode, la gravure avant la découpe
RANG_MIXTE = 2  # un calque/groupe avec les 2 opérations passe après les autres


################################################################################
#
# Point d'entrée : svg = racine du document, type_chemin = fonction(chemin) -> "grav", "cut" ou None
# Retourne le nombre de calques/groupes et de chemins déplacés
#
################################################################################
def reordonner(svg, type_chemin):
    stats = {"groupes": 0, "chemins": 0}
    _traiter(svg, type_chemin, stats)
    return stats


################################################################################
#
# Traite un conteneur : range d'abord ses enfants, puis lui même
# Retourne l'ensemble des opérations contenues ({"grav"}, {"cut"}, les 2 ou vide)
#
################################################################################
def _traiter(conteneur, type_chemin, stats):
    types = set()
    enfants = list(conteneur)
    groupes = []  # (index, élément, rang)
    chemins = []

    for index, el in enumerate(enfants):
        if isinstance(el, Group):
            if el.get(ATTR_IGNORE) is not None or el.style("display") != "inline":
                continue
            sous_types = _traiter(el, type_chemin, stats)
            if sous_types:
                types |= sous_types
                groupes.append((index, el, _rang_groupe(sous_types)))
        elif isinstance(el, PathElement) and isinstance(conteneur, Group):
            if el.get(ATTR_IGNORE) is not None:
                continue
            t = type_chemin(el)
            if t is not None:
                types.add(t)
                chemins.append((index, el, RANG[t]))

    stats["groupes"] += _permuter(conteneur, enfants, groupes)
    stats["chemins"] += _permuter(conteneur, enfants, chemins)
    return types


def _rang_groupe(types):
    if len(types) > 1:
        return RANG_MIXTE
    return RANG[next(iter(types))]


################################################################################
#
# Remet les éléments de pool dans les emplacements qu'ils occupent déjà, triés par rang
# pool = [(index, élément, rang)] dans l'ordre du XML. Retourne le nombre d'éléments déplacés
#
################################################################################
def _permuter(conteneur, enfants, pool):
    if len(pool) < 2:
        return 0
    emplacements = [p[0] for p in pool]
    ordre_gcode = sorted(reversed(pool), key=lambda p: p[2])  # tri stable sur l'ordre actuel du gcode
    nouveau_xml = list(reversed(ordre_gcode))

    ordre = list(enfants)
    deplaces = 0
    for emplacement, p in zip(emplacements, nouveau_xml):
        if ordre[emplacement] is not p[1]:
            deplaces += 1
        ordre[emplacement] = p[1]

    if deplaces:
        for position, el in enumerate(ordre):
            conteneur.insert(position, el)
        # les enfants du conteneur ont changé de place, la liste de l'appelant n'est plus valable
        enfants[:] = ordre
    return deplaces
