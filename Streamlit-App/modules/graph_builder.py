"""Module de construction de graphes avec Pyvis."""
from pyvis.network import Network
import re
import hashlib


def hex_to_rgba(hex_color):
    """Convertit une couleur hexadécimale en RGBA.

    Args:
        hex_color: Couleur au format hexadécimal (#RRGGBB ou #RRGGBBAA)

    Returns:
        Couleur au format rgba() ou la valeur d'origine si non applicable
    """
    if not isinstance(hex_color, str):
        return hex_color
    s = hex_color.strip()
    m8 = re.match(r'^#([0-9a-fA-F]{8})$', s)
    m6 = re.match(r'^#([0-9a-fA-F]{6})$', s)
    if m8:
        hexa = m8.group(1)
        r = int(hexa[0:2], 16)
        g = int(hexa[2:4], 16)
        b = int(hexa[4:6], 16)
        a = int(hexa[6:8], 16) / 255
        return f"rgba({r}, {g}, {b}, {a:.2f})"
    if m6:
        return s
    return s


def clean_value(raw):
    """Nettoie une valeur en supprimant les guillemets et espaces.

    Args:
        raw: Valeur brute à nettoyer

    Returns:
        Valeur nettoyée
    """
    if raw is None:
        return raw
    v = raw.strip()
    if ((v.startswith('"') and v.endswith('"')) or
            (v.startswith("'") and v.endswith("'"))):
        v = v[1:-1]
    return v.strip()


def parse_style_grass(file_path):
    """Parse un fichier .grass de Neo4j pour en extraire les styles.

    Args:
        file_path: Chemin vers le fichier .grass

    Returns:
        Dictionnaire contenant les styles par label
    """
    label_styles = {}
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = r'(node(?:\.\*|(?:\.[A-Za-z0-9_]+))?\s*\{.*?\})'
    node_blocks = re.findall(pattern, content, re.DOTALL)
    for block in node_blocks:
        m = re.match(r'node(?:\.([A-Za-z0-9_]+)|\.\*)?\s*\{', block)
        label_raw = m.group(1) if m and m.group(1) else "*"
        label = label_raw.lower()
        props = {}
        prop_pattern = r'([A-Za-z0-9_-]+)\s*:\s*([^;]+);'
        for k, v in re.findall(prop_pattern, block):
            props[k] = clean_value(v)
        label_styles[label] = props

    rel_blocks = re.findall(
        r'(relationship(?:\.[A-Za-z0-9_]+)?\s*\{.*?\})',
        content,
        re.DOTALL
    )
    for block in rel_blocks:
        m = re.match(r'relationship(?:\.([A-Za-z0-9_]+))?\s*\{', block)
        rel_type = m.group(1).upper() if m and m.group(1) else "relationship"
        props = {}
        prop_pattern = r'([A-Za-z0-9_-]+)\s*:\s*([^;]+);'
        for k, v in re.findall(prop_pattern, block):
            props[k] = clean_value(v)
        label_styles[rel_type] = props

    return label_styles


def apply_caption_template(caption_template, node_props):
    """Applique un template de caption aux propriétés d'un nœud.

    Args:
        caption_template: Template de caption avec des placeholders {key}
        node_props: Propriétés du nœud

    Returns:
        Caption avec les valeurs remplacées
    """
    if not caption_template:
        return None
    tpl = caption_template

    def repl(match):
        key = match.group(1)
        return str(node_props.get(key, ""))
    tpl = re.sub(r'\{([^}]+)\}', repl, tpl)
    return tpl


def _to_int_px(value, fallback=20):
    """Convertit une valeur en pixels entiers.

    Args:
        value: Valeur à convertir (peut contenir 'px')
        fallback: Valeur par défaut si conversion impossible

    Returns:
        Valeur en pixels (int)
    """
    if not value:
        return fallback
    v = str(value).strip()
    m = re.match(r'(\d+)', v)
    if m:
        try:
            return int(m.group(1))
        except ValueError:
            return fallback
    return fallback


def color_from_label(label):
    """Génère une couleur unique basée sur le label.

    Args:
        label: Label pour lequel générer une couleur

    Returns:
        Couleur au format rgb()
    """
    h = hashlib.md5(label.encode("utf-8")).hexdigest()
    r = int(h[0:2], 16)
    g = int(h[2:4], 16)
    b = int(h[4:6], 16)
    return f"rgb({r},{g},{b})"


def _extract_node_labels(node):
    """Extrait les labels d'un nœud.

    Args:
        node: Dictionnaire représentant un nœud

    Returns:
        Liste des labels du nœud
    """
    for key in ("label", "labels"):
        if key in node:
            val = node.get(key)
            if val is None:
                return []
            if isinstance(val, list):
                return [str(x) for x in val if x is not None]
            return [str(val)]
    return []


def build_pyvis_graph(nodes, relationships, height="600px",
                      style_file=None, label_map=None, debug=False):
    """Construit un graphe interactif avec Pyvis.

    Args:
        nodes: Liste des nœuds du graphe
        relationships: Liste des relations du graphe
        height: Hauteur du graphe (défaut: "600px")
        style_file: Chemin vers fichier .grass de styles (optionnel)
        label_map: Mapping de labels personnalisé (optionnel)
        debug: Active le mode debug (défaut: False)

    Returns:
        HTML du graphe ou dict avec 'html' et 'debug' si debug=True
    """
    net = Network(height=height, width="100%", directed=True)
    net.force_atlas_2based()

    label_styles = {}
    if style_file:
        label_styles = parse_style_grass(style_file)

    label_map = {k.lower(): v.lower() for k, v in (label_map or {}).items()}

    debug_list = []

    # Mapper chaque element_id (string complexe) vers un entier simple
    # pour éviter tout problème de vis.js avec les caractères spéciaux
    id_map = {node["id"]: idx for idx, node in enumerate(nodes)}

    for node in nodes:
        raw_label_list = _extract_node_labels(node)
        raw_lower = [low.lower() for low in raw_label_list]

        # Appliquer mapping si fourni
        mapped = []
        for rl in raw_lower:
            mapped.append(label_map.get(rl, rl))
        chosen_label = None
        for mp in mapped:
            if mp in label_styles:
                chosen_label = mp
                break
        if chosen_label is None and "*" in label_styles:
            chosen_label = "*"

        style = label_styles.get(chosen_label, {})

        # Couleurs
        if style and "color" in style:
            bg_color = hex_to_rgba(style.get("color"))
            border_color = hex_to_rgba(
                style.get("border-color", "#000000")
            )
        else:
            # génération automatique si pas de style spécifique
            label_for_color = (
                raw_lower[0] if raw_lower else str(node.get("id"))
            )
            bg_color = color_from_label(label_for_color)
            border_color = bg_color

        text_color_internal = (
            style.get("text-color-internal") or
            style.get("text-color") or
            "#000000"
        )

        # Taille (size ou diameter) et bord
        size = _to_int_px(
            style.get("diameter", style.get("size", None)), fallback=25
        )
        border_width = _to_int_px(style.get("border-width", None), fallback=2)

        # Caption : privilégier le champ 'name' ou template du .grass
        caption_template = (
            style.get("caption") or style.get("defaultCaption")
        )
        caption = None
        if caption_template:
            caption = apply_caption_template(caption_template, node)
        # priorité: champ name > title > id > caption_template
        caption = (
            node.get("name") or
            node.get("title") or
            caption or
            str(node.get("id"))
        )

        # Ajuster police: taille en fonction du diamètre
        # font.size correspond à px dans vis.js
        font_size = max(10, int(size / 3))
        font_color = text_color_internal

        # Créer l'argument color pour vis.js (background + border)
        color_arg = {
            "background": bg_color,
            "border": border_color,
            "highlight": {"background": bg_color, "border": border_color},
            "hover": {"background": bg_color, "border": border_color}
        }

        # Créer le titre avec toutes les propriétés sauf id, label, labels
        properties = [
            f"{k}: {v}" for k, v in node.items()
            if k not in ("id", "label", "labels")
        ]
        title = "<br>".join(properties)

        net.add_node(
            id_map[node["id"]],
            label=caption,
            title=title,
            color=color_arg,
            size=size,
            borderWidth=border_width,
            font={
                "color": font_color,
                "size": font_size,
                "face": "Arial",
                "align": "center"
            }
        )

        debug_list.append({
            "id": node.get("id"),
            "pyvis_id": id_map[node["id"]],
            "raw_labels": raw_label_list,
            "chosen_label": chosen_label,
            "caption": caption,
            "bg_color": bg_color,
            "border_color": border_color,
            "size": size,
            "font_size": font_size
        })

    # Relations
    # Style global de fallback
    default_rel_style = label_styles.get("relationship", {})
    default_rel_color = hex_to_rgba(
        default_rel_style.get("color", "#000000")
    )
    default_rel_width = _to_int_px(
        default_rel_style.get("shaft-width", None), fallback=2
    )

    # Construire le set des IDs connus depuis la liste d'entrée
    # (plus fiable que net.get_nodes() qui peut convertir les types)
    known_node_ids = {node["id"] for node in nodes}

    for rel in relationships:
        source_id = rel["source"]
        target_id = rel["target"]
        rel_type = rel.get("type", "")

        if source_id not in known_node_ids or target_id not in known_node_ids:
            continue

        # Chercher le style spécifique du type de relation (ex: DIRECTED)
        specific_style = label_styles.get(rel_type.upper(), {})
        rel_color = hex_to_rgba(
            specific_style.get("color", default_rel_color)
        )
        rel_width = _to_int_px(
            specific_style.get("shaft-width",
                               specific_style.get("width", None)),
            fallback=default_rel_width
        )

        net.add_edge(
            id_map[source_id],
            id_map[target_id],
            label=rel_type,
            color=rel_color,
            width=rel_width
        )

    # Options : shape circle et police par défaut
    net.set_options("""
    var options = {
      "nodes": {
        "shape": "circle",
        "font": {"multi": false, "face": "Arial"}
      },
      "edges": {"arrows": {"to": {"enabled": true}}},
      "physics": {"forceAtlas2Based": {"gravitationalConstant": -50}}
    }
    """)
    html = net.generate_html()
    if debug:
        return {"html": html, "debug": debug_list}
    return html
