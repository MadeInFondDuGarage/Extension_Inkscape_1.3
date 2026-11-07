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
# Étape 1 : ordre des calques/groupes entre eux (seuls les calques/groupes visibles et les chemins
#           visibles de couleur reconnue sont pris en compte)
#   - calque/groupe de gravure seule   : en premier dans le gcode
#   - calque/groupe de découpe seule   : ensuite
#   - calque/groupe qui mélange les 2  : en dernier dans le gcode (le plus en arrière plan dans Inkscape)
#
# Étape 2 : parcours des chemins dans chaque calque/groupe, en suivant l'ordre du gcode
#   - la gravure puis la découpe
#   - dans chaque outil, le parcours le plus court : départ du bloc = fin du bloc précédent
#     (le tout premier bloc part de "depart"), tour glouton puis amélioration 2-opt
#   - le sens d'un chemin ouvert est inversé si cela raccourcit le parcours
#   - un chemin fermé n'est jamais modifié (point de départ et sens conservés)
#   - un chemin avec un effet de chemin (LPE) n'est jamais inversé, seulement déplacé
#
# Les autres éléments (invisibles, couleur non reconnue, orientation, aperçu...) gardent leur place.
# Le réordonnancement se fait entre éléments de même parent, la hiérarchie n'est jamais modifiée.
#
# Module construit et débugger avec l'aide de "Claude code"
#
################################################################################
import math
import time

from inkex import Group, PathElement

ATTR_IGNORE = "Path2Laser"  # attribut des groupes créés par l'extension (orientation, aperçu)
RANG = {"grav": 0, "cut": 1}  # ordre dans le gcode, la gravure avant la découpe
RANG_MIXTE = 2  # un calque/groupe avec les 2 opérations passe après les autres
TOLERANCE = 1e-6  # écart maxi pour considérer 2 points identiques (unités du document)
DELAI_AMELIORATION = 5.0  # secondes maxi par calque/groupe et par outil pour l'amélioration 2-opt


################################################################################
#
# Point d'entrée
#   svg         : racine du document
#   type_chemin : fonction(chemin) -> "grav", "cut" ou None
#   depart      : position de départ de la machine dans le document (x, y), en unités du document
# Retourne un dictionnaire : nombre de calques/groupes et de chemins déplacés, chemins inversés,
# longueur des déplacements à vide avant et après (en mm)
#
################################################################################
def reordonner(svg, type_chemin, depart=(0.0, 0.0)):
    stats = {"groupes": 0, "chemins": 0, "inverses": 0}
    _ordonner_groupes(svg, type_chemin, stats)

    contexte = {"avant": depart, "apres": depart, "dist_avant": 0.0, "dist_apres": 0.0}
    _parcourir(svg, type_chemin, contexte, stats)

    echelle = svg.unittouu("1mm") or 1.0  # unités du document par mm
    stats["mm_avant"] = contexte["dist_avant"] / echelle
    stats["mm_apres"] = contexte["dist_apres"] / echelle
    return stats


################################################################################
#
# Étape 1 : ordre des calques/groupes
# Range d'abord les enfants d'un conteneur, puis le conteneur lui même
# Retourne l'ensemble des opérations contenues ({"grav"}, {"cut"}, les 2 ou vide)
#
################################################################################
def _ordonner_groupes(conteneur, type_chemin, stats):
    types = set()
    enfants = list(conteneur)
    groupes = []  # (index, élément, rang)

    for index, el in enumerate(enfants):# je récupère tous les chemin des groupes qui est ensuite mis dans une list
        if _groupe_visible(el):
            sous_types = _ordonner_groupes(el, type_chemin, stats)
            if sous_types:
                types |= sous_types
                groupes.append((index, el, _rang_groupe(sous_types))) # dans la liste je met un tupple avec l'index, le groupe/calque et le rang (donc 0,1,2 suivant si gravure/découpe)
        elif isinstance(el, PathElement) and isinstance(conteneur, Group) and el.get(ATTR_IGNORE) is None:
            t = type_chemin(el)
            if t is not None:
                types.add(t)

    # ordre actuel du gcode = XML inversé, tri stable sur cet ordre
    ordre_gcode = sorted(reversed(groupes), key=lambda g: g[2])# ici je réordonne les calcque groupes via le sorted d'un liste en s'appuyant sur le rang qui est la 3 eme info du tupple donc g[2]
    stats["groupes"] += _ecrire_ordre(conteneur, enfants, [g[0] for g in groupes], [g[1] for g in reversed(ordre_gcode)])
    return types


def _groupe_visible(el):
    return isinstance(el, Group) and el.get(ATTR_IGNORE) is None and el.style("display") == "inline"


def _rang_groupe(types):
    if len(types) > 1:
        return RANG_MIXTE
    return RANG[next(iter(types))]


################################################################################
#
# Étape 2 : parcours des chemins, dans l'ordre de lecture du gcode
# Un conteneur passe avant ses enfants, les enfants sont lus du dernier au premier
#
################################################################################
def _parcourir(conteneur, type_chemin, contexte, stats):
    if isinstance(conteneur, Group):
        _optimiser_bloc(conteneur, type_chemin, contexte, stats)
    for el in reversed(list(conteneur)):
        if _groupe_visible(el):
            _parcourir(el, type_chemin, contexte, stats)


################################################################################
#
# Optimise les chemins qui appartiennent directement à un calque/groupe
#
################################################################################
def _optimiser_bloc(groupe, type_chemin, contexte, stats):
    enfants = list(groupe)
    pool = []  # (index, élément, type, (début, fin, inversion impossible))
    for index, el in enumerate(enfants):
        if isinstance(el, PathElement) and el.get(ATTR_IGNORE) is None:
            t = type_chemin(el)
            extremites = _extremites(el) if t is not None else None
            if extremites is not None:
                pool.append((index, el, t, extremites))
    if not pool:
        return

    ordre_actuel = list(reversed(pool))  # ordre actuel du gcode
    final = []  # (élément, inversé)
    for outil in ("grav", "cut"):
        du_outil = [p for p in ordre_actuel if p[2] == outil]
        if not du_outil:
            continue
        items = [p[3] for p in du_outil]

        # déplacements à vide si on ne change rien
        contexte["dist_avant"] += _cout(items, [(k, False) for k in range(len(items))], contexte["avant"])
        contexte["avant"] = items[-1][1]

        # déplacements à vide avec le meilleur parcours
        tour = _meilleur_tour(items, contexte["apres"])
        contexte["dist_apres"] += _cout(items, tour, contexte["apres"])
        contexte["apres"] = _sortie(items, tour[-1])
        final += [(du_outil[k][1], inverse) for k, inverse in tour]

    for el, inverse in final:
        if inverse and _inverser(el):
            stats["inverses"] += 1
    # l'ordre du gcode est l'inverse de l'ordre XML
    stats["chemins"] += _ecrire_ordre(groupe, enfants, [p[0] for p in pool], [el for el, _ in reversed(final)])


################################################################################
#
# Début, fin d'un chemin en coordonnées du document (transformations des parents comprises)
# Retourne (début, fin, inversion impossible) ou None si le chemin est vide
# Un chemin fermé (début = fin) ne peut pas être amélioré par une inversion, donc jamais bloqué
#
################################################################################
def _extremites(el):
    csp = el.path.to_superpath()
    if not csp or not csp[0]:
        return None
    transformation = el.composed_transform()
    debut = transformation.apply_to_point(csp[0][0][1])
    fin = transformation.apply_to_point(csp[-1][-1][1])
    debut = (debut[0], debut[1])
    fin = (fin[0], fin[1])
    ferme = _dist(debut, fin) < TOLERANCE
    effet = el.get("inkscape:path-effect") is not None or el.get("inkscape:original-d") is not None
    return (debut, fin, effet and not ferme)


################################################################################
#
# Inverse le sens d'un chemin, le résultat est vérifié, sinon le chemin n'est pas modifié
# Retourne True si le chemin a été inversé
#
################################################################################
def _inverser(el):
    avant = el.path
    apres = avant.reverse()
    csp_avant = avant.to_superpath()
    csp_apres = apres.to_superpath()
    if not csp_apres or not csp_apres[0]:
        return False
    if (_dist(csp_avant[0][0][1], csp_apres[-1][-1][1]) > TOLERANCE
            or _dist(csp_avant[-1][-1][1], csp_apres[0][0][1]) > TOLERANCE):
        return False
    if _dist(csp_avant[0][0][1], csp_avant[-1][-1][1]) < TOLERANCE:
        return False  # chemin fermé, rien à gagner
    el.path = apres
    types_noeuds = el.get("sodipodi:nodetypes")
    if types_noeuds:
        el.set("sodipodi:nodetypes", types_noeuds[::-1])
    return True


################################################################################
#
# Parcours : liste de (numéro d'item, inversé)
# items = [(début, fin, inversion impossible)]
#
################################################################################
def _entree(items, element):
    return items[element[0]][1] if element[1] else items[element[0]][0]


def _sortie(items, element):
    return items[element[0]][0] if element[1] else items[element[0]][1]


def _dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _cout(items, tour, position):
    total = 0.0
    for element in tour:
        total += _dist(position, _entree(items, element))
        position = _sortie(items, element)
    return total


# meilleur résultat entre l'ordre actuel et un tour glouton, tous les 2 améliorés
def _meilleur_tour(items, position):
    debut = time.monotonic()
    actuel = _ameliorer(items, [(k, False) for k in range(len(items))], position, debut + DELAI_AMELIORATION / 2)
    glouton = _ameliorer(items, _glouton(items, position), position, debut + DELAI_AMELIORATION)
    if _cout(items, glouton, position) < _cout(items, actuel, position) - 1e-9:
        return glouton
    return actuel


# plus proche voisin, avec inversion du chemin si sa fin est plus proche que son début
def _glouton(items, position):
    restant = list(range(len(items)))
    tour = []
    while restant:
        meilleur = None
        for k in restant:
            debut, fin, bloque = items[k]
            d_debut = _dist(position, debut)
            d_fin = float("inf") if bloque else _dist(position, fin)
            candidat = (d_debut, k, False) if d_debut <= d_fin else (d_fin, k, True)
            if meilleur is None or candidat[0] < meilleur[0]:
                meilleur = candidat
        _, k, inverse = meilleur
        restant.remove(k)
        tour.append((k, inverse))
        position = items[k][0] if inverse else items[k][1]
    return tour


# 2-opt : on inverse une suite de chemins (ordre et sens) tant que cela raccourcit le parcours
def _ameliorer(items, tour, position, limite):
    n = len(tour)
    amelioration = True
    while amelioration and time.monotonic() < limite:
        amelioration = False
        bloques = _cumul_bloques(items, tour)
        for i in range(n):
            if time.monotonic() > limite:
                break
            gauche = position if i == 0 else _sortie(items, tour[i - 1])
            premier = _entree(items, tour[i])
            for j in range(i, n):
                if bloques[j + 1] - bloques[i] > 0:
                    break
                dernier = _sortie(items, tour[j])
                if j + 1 < n:
                    droite = _entree(items, tour[j + 1])
                    ancien = _dist(gauche, premier) + _dist(dernier, droite)
                    nouveau = _dist(gauche, dernier) + _dist(premier, droite)
                else:
                    ancien = _dist(gauche, premier)
                    nouveau = _dist(gauche, dernier)
                if nouveau < ancien - 1e-9:
                    tour[i:j + 1] = [(k, not inverse) for k, inverse in reversed(tour[i:j + 1])]
                    amelioration = True
                    premier = _entree(items, tour[i])
                    bloques = _cumul_bloques(items, tour)
    return tour


# nombre cumulé de chemins qu'on ne peut pas inverser
def _cumul_bloques(items, tour):
    cumul = [0]
    for element in tour:
        cumul.append(cumul[-1] + (1 if items[element[0]][2] else 0))
    return cumul


################################################################################
#
# Remet des éléments dans les emplacements (index d'enfants) qu'ils occupent déjà
# emplacements en ordre croissant, elements dans l'ordre XML souhaité
# Retourne le nombre d'éléments déplacés
#
################################################################################
def _ecrire_ordre(conteneur, enfants, emplacements, elements):
    ordre = list(enfants)
    deplaces = 0
    for emplacement, el in zip(emplacements, elements):
        if ordre[emplacement] is not el:
            deplaces += 1
        ordre[emplacement] = el

    if deplaces:
        for position, el in enumerate(ordre):
            conteneur.insert(position, el)
        # la liste de l'appelant n'est plus valable après le déplacement
        enfants[:] = ordre
    return deplaces
