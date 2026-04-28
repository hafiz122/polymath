"""SVG polygon and angle diagram renderer."""
import math
from typing import List, Tuple, Optional


# Color palette for beautiful diagrams (dark colors for light theme visibility)
COLORS = {
    "polygon_stroke": "#1a1a1a",
    "polygon_fill": "rgba(13, 115, 119, 0.08)",
    "polygon_fill_highlight": "rgba(194, 65, 12, 0.10)",
    "angle_arc": "#c2410c",
    "angle_arc_missing": "#d97706",
    "label": "#1a1a1a",
    "label_highlight": "#c2410c",
    "grid": "rgba(0, 0, 0, 0.06)",
    "vertex": "#1a1a1a",
    "vertex_highlight": "#c2410c",
}


def _polygon_vertices(
    sides: int,
    cx: float = 200,
    cy: float = 200,
    radius: float = 140,
    rotation: float = -math.pi / 2,
) -> List[Tuple[float, float]]:
    """Return list of (x, y) vertices for a regular polygon."""
    vertices = []
    for i in range(sides):
        angle = rotation + 2 * math.pi * i / sides
        x = cx + radius * math.cos(angle)
        y = cy + radius * math.sin(angle)
        vertices.append((x, y))
    return vertices


def _svg_header(width: int = 400, height: int = 400) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="100%" height="100%" style="max-width:{width}px;max-height:{height}px;">'
    )


def _svg_footer() -> str:
    return "</svg>"


def _draw_grid(width: int = 400, height: int = 400, step: int = 20) -> str:
    """Draw a subtle grid background."""
    lines = []
    for x in range(0, width + 1, step):
        lines.append(
            f'<line x1="{x}" y1="0" x2="{x}" y2="{height}" stroke="{COLORS["grid"]}" stroke-width="0.5"/>'
        )
    for y in range(0, height + 1, step):
        lines.append(
            f'<line x1="0" y1="{y}" x2="{width}" y2="{y}" stroke="{COLORS["grid"]}" stroke-width="0.5"/>'
        )
    return "\n".join(lines)


def _draw_polygon(
    vertices: List[Tuple[float, float]],
    fill: str = None,
    stroke: str = None,
    stroke_width: float = 2.5,
    dashed: bool = False,
) -> str:
    points = " ".join(f"{x:.2f},{y:.2f}" for x, y in vertices)
    fill = fill or COLORS["polygon_fill"]
    stroke = stroke or COLORS["polygon_stroke"]
    dash_attr = ' stroke-dasharray="6,4"' if dashed else ""
    return (
        f'<polygon points="{points}" fill="{fill}" stroke="{stroke}" '
        f'stroke-width="{stroke_width}" stroke-linejoin="round"{dash_attr}/>'
    )


def _draw_angle_arc(
    vertex: Tuple[float, float],
    prev_vertex: Tuple[float, float],
    next_vertex: Tuple[float, float],
    arc_radius: float = 28,
    color: str = None,
    stroke_width: float = 2.5,
) -> str:
    """Draw an interior angle arc at a vertex."""
    vx, vy = vertex
    px, py = prev_vertex
    nx, ny = next_vertex

    # Vectors from vertex to neighbors
    v1x, v1y = px - vx, py - vy
    v2x, v2y = nx - vx, ny - vy

    # Normalize
    len1 = math.hypot(v1x, v1y)
    len2 = math.hypot(v2x, v2y)
    if len1 == 0 or len2 == 0:
        return ""
    v1x, v1y = v1x / len1, v1y / len1
    v2x, v2y = v2x / len2, v2y / len2

    # Arc endpoints
    start_x = vx + v1x * arc_radius
    start_y = vy + v1y * arc_radius
    end_x = vx + v2x * arc_radius
    end_y = vy + v2y * arc_radius

    # Determine large-arc-flag (0 for convex polygon interior angles < 180)
    cross = v1x * v2y - v1y * v2x
    dot = v1x * v2x + v1y * v2y
    interior_angle = math.atan2(abs(cross), dot)
    large_arc = 1 if interior_angle > math.pi else 0

    color = color or COLORS["angle_arc"]
    sweep = 1 if cross > 0 else 0

    return (
        f'<path d="M {start_x:.2f} {start_y:.2f} A {arc_radius:.2f} {arc_radius:.2f} 0 '
        f'{large_arc} {sweep} {end_x:.2f} {end_y:.2f}" fill="none" stroke="{color}" '
        f'stroke-width="{stroke_width}" stroke-linecap="round"/>'
    )


def _draw_vertex_dot(
    vertex: Tuple[float, float],
    color: str = None,
    radius: float = 4,
) -> str:
    x, y = vertex
    color = color or COLORS["vertex"]
    return f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{radius}" fill="{color}"/>'


def _draw_label(
    pos: Tuple[float, float],
    text: str,
    color: str = None,
    font_size: int = 15,
    bold: bool = False,
) -> str:
    x, y = pos
    color = color or COLORS["label"]
    weight = "bold" if bold else "normal"
    # Use a serif font stack for LaTeX-like appearance
    font_family = "'Latin Modern Math', 'Times New Roman', serif"
    return (
        f'<text x="{x:.2f}" y="{y:.2f}" fill="{color}" font-size="{font_size}" '
        f'font-family="{font_family}" font-weight="{weight}" text-anchor="middle" '
        f'dominant-baseline="middle">{text}</text>'
    )


def _label_position_for_vertex(
    vertex: Tuple[float, float],
    prev_vertex: Tuple[float, float],
    next_vertex: Tuple[float, float],
    offset: float = 42,
) -> Tuple[float, float]:
    """Compute label position slightly outside the interior angle bisector."""
    vx, vy = vertex
    px, py = prev_vertex
    nx, ny = next_vertex

    v1x, v1y = px - vx, py - vy
    v2x, v2y = nx - vx, ny - vy

    len1 = math.hypot(v1x, v1y)
    len2 = math.hypot(v2x, v2y)
    if len1 == 0 or len2 == 0:
        return (vx, vy - offset)

    v1x, v1y = v1x / len1, v1y / len1
    v2x, v2y = v2x / len2, v2y / len2

    # Bisector pointing inside polygon
    bx, by = v1x + v2x, v1y + v2y
    blen = math.hypot(bx, by)
    if blen == 0:
        return (vx, vy - offset)
    bx, by = bx / blen, by / blen

    return (vx + bx * offset, vy + by * offset)


def render_polygon_with_angles(
    sides: int,
    labels: List[Optional[str]],
    highlight_indices: Optional[List[int]] = None,
    rotation: float = -math.pi / 2,
    show_grid: bool = True,
) -> str:
    """
    Render a regular polygon with angle labels.
    
    Args:
        sides: Number of sides
        labels: List of strings/None for each vertex angle. None = no label.
        highlight_indices: Vertex indices to highlight (e.g., the missing angle).
        rotation: Initial rotation in radians.
        show_grid: Whether to show background grid.
    """
    if len(labels) != sides:
        raise ValueError("labels length must match sides")

    highlight_indices = highlight_indices or []
    vertices = _polygon_vertices(sides, rotation=rotation)
    parts = [_svg_header()]

    if show_grid:
        parts.append(_draw_grid())

    # Draw polygon
    fill = COLORS["polygon_fill_highlight"] if highlight_indices else COLORS["polygon_fill"]
    parts.append(_draw_polygon(vertices, fill=fill))

    # Draw angle arcs and labels
    for i in range(sides):
        prev_v = vertices[(i - 1) % sides]
        curr_v = vertices[i]
        next_v = vertices[(i + 1) % sides]

        is_highlight = i in highlight_indices
        arc_color = COLORS["angle_arc_missing"] if is_highlight else COLORS["angle_arc"]
        label_color = COLORS["label_highlight"] if is_highlight else COLORS["label"]

        parts.append(_draw_angle_arc(curr_v, prev_v, next_v, color=arc_color))

        if labels[i] is not None:
            lx, ly = _label_position_for_vertex(curr_v, prev_v, next_v)
            parts.append(_draw_label((lx, ly), labels[i], color=label_color, bold=is_highlight))

        parts.append(_draw_vertex_dot(curr_v, color=COLORS["vertex_highlight"] if is_highlight else COLORS["vertex"]))

    parts.append(_svg_footer())
    return "\n".join(parts)


def render_simple_polygon(
    sides: int,
    label: Optional[str] = None,
    rotation: float = -math.pi / 2,
    show_grid: bool = True,
) -> str:
    """Render a simple regular polygon, optionally with a center label."""
    vertices = _polygon_vertices(sides, rotation=rotation)
    parts = [_svg_header()]

    if show_grid:
        parts.append(_draw_grid())

    parts.append(_draw_polygon(vertices, fill=COLORS["polygon_fill"]))

    for v in vertices:
        parts.append(_draw_vertex_dot(v))

    # Draw side tick marks for regular polygons
    for i in range(sides):
        v1 = vertices[i]
        v2 = vertices[(i + 1) % sides]
        mx = (v1[0] + v2[0]) / 2
        my = (v1[1] + v2[1]) / 2
        # Small tick perpendicular to side
        dx = v2[0] - v1[0]
        dy = v2[1] - v1[1]
        length = math.hypot(dx, dy)
        if length > 0:
            nx, ny = -dy / length, dx / length
            tick_len = 8
            parts.append(
                f'<line x1="{mx + nx * tick_len:.2f}" y1="{my + ny * tick_len:.2f}" '
                f'x2="{mx - nx * tick_len:.2f}" y2="{my - ny * tick_len:.2f}" '
                f'stroke="{COLORS["polygon_stroke"]}" stroke-width="1.5"/>'
            )

    if label:
        parts.append(_draw_label((200, 200), label, font_size=18, bold=True))

    parts.append(_svg_footer())
    return "\n".join(parts)


def render_triangle_with_angles(
    angles: List[Optional[float]],
    missing_index: Optional[int] = None,
) -> str:
    """Render a triangle with angle labels. Angles in degrees."""
    labels = []
    for i, a in enumerate(angles):
        if a is None or (missing_index is not None and i == missing_index):
            labels.append("?")
        else:
            labels.append(f"{a:.0f}°")
    return render_polygon_with_angles(3, labels, highlight_indices=[missing_index] if missing_index is not None else [])


def render_quadrilateral_with_angles(
    angles: List[Optional[float]],
    missing_index: Optional[int] = None,
) -> str:
    """Render a quadrilateral with angle labels. Angles in degrees."""
    labels = []
    for i, a in enumerate(angles):
        if a is None or (missing_index is not None and i == missing_index):
            labels.append("?")
        else:
            labels.append(f"{a:.0f}°")
    return render_polygon_with_angles(4, labels, highlight_indices=[missing_index] if missing_index is not None else [])
