"""Problem generator for polygon geometry topics."""
import math
import random
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from game.renderer import (
    render_polygon_with_angles,
    render_simple_polygon,
    render_triangle_with_angles,
    render_quadrilateral_with_angles,
)


@dataclass
class Problem:
    question: str
    question_latex: str
    svg_markup: str
    options: List[str]
    correct_answer: str
    explanation: str
    difficulty: int  # 1-3
    topic: str


# Polygon names
POLYGON_NAMES = {
    3: "Triangle",
    4: "Quadrilateral",
    5: "Pentagon",
    6: "Hexagon",
    7: "Heptagon",
    8: "Octagon",
    9: "Nonagon",
    10: "Decagon",
    11: "Hendecagon",
    12: "Dodecagon",
}


def _shuffle_options(answer: str, distractors: List[str]) -> List[str]:
    opts = [answer] + distractors
    random.shuffle(opts)
    return opts


def _distractors_around(value: int, count: int = 3, spread: int = 30, exclude: Optional[List[int]] = None) -> List[str]:
    """Generate numeric distractors around a value."""
    exclude = exclude or []
    distractors = set()
    attempts = 0
    while len(distractors) < count and attempts < 100:
        d = value + random.randint(-spread, spread)
        if d != value and d > 0 and d not in exclude:
            distractors.add(d)
        attempts += 1
    return [str(x) for x in distractors]


def _distractors_from_pool(answer: str, pool: List[str], count: int = 3) -> List[str]:
    pool = [p for p in pool if p != answer]
    if len(pool) <= count:
        return pool
    return random.sample(pool, count)


# ---------------------------------------------------------------------------
# Problem type generators
# ---------------------------------------------------------------------------

def _gen_missing_triangle_angle(difficulty: int = 1) -> Problem:
    """Triangle with two angles given, find the third."""
    a = random.randint(30, 80)
    b = random.randint(30, 80)
    c = 180 - a - b
    while c <= 10 or c >= 170:
        a = random.randint(30, 80)
        b = random.randint(30, 80)
        c = 180 - a - b

    missing = random.randint(0, 2)
    angles = [a, b, c]
    labels = [float(angles[i]) if i != missing else None for i in range(3)]

    svg = render_triangle_with_angles(labels, missing_index=missing)
    answer = str(c if missing == 2 else (a if missing == 0 else b))

    question = "Find the missing angle in this triangle."
    question_latex = r"\text{Find the missing angle in this triangle.}"
    explanation = (
        f"The sum of angles in a triangle is $180^{{\\circ}}$. "
        f"Given angles are ${a}^{{\\circ}}$ and ${b}^{{\\circ}}$, so the missing angle is "
        f"$180 - {a} - {b} = {answer}^{{\\circ}}$."
    )
    return Problem(
        question=question,
        question_latex=question_latex,
        svg_markup=svg,
        options=_shuffle_options(f"{answer}°", [f"{d}°" for d in _distractors_around(int(answer), spread=25)]),
        correct_answer=f"{answer}°",
        explanation=explanation,
        difficulty=difficulty,
        topic="missing_angle",
    )


def _gen_missing_quadrilateral_angle(difficulty: int = 2) -> Problem:
    """Quadrilateral with three angles given, find the fourth."""
    a = random.randint(60, 120)
    b = random.randint(60, 120)
    c = random.randint(60, 120)
    d = 360 - a - b - c
    while d <= 20 or d >= 300:
        a = random.randint(60, 120)
        b = random.randint(60, 120)
        c = random.randint(60, 120)
        d = 360 - a - b - c

    missing = random.randint(0, 3)
    angles = [a, b, c, d]
    labels = [float(angles[i]) if i != missing else None for i in range(4)]

    svg = render_quadrilateral_with_angles(labels, missing_index=missing)
    answer = str(angles[missing])

    question = "Find the missing angle in this quadrilateral."
    question_latex = r"\text{Find the missing angle in this quadrilateral.}"
    explanation = (
        f"The sum of interior angles in a quadrilateral is $360^{{\\circ}}$. "
        f"Given angles are ${a}^{{\\circ}}$, ${b}^{{\\circ}}$, and ${c}^{{\\circ}}$, so the missing angle is "
        f"$360 - {a} - {b} - {c} = {answer}^{{\\circ}}$."
    )
    return Problem(
        question=question,
        question_latex=question_latex,
        svg_markup=svg,
        options=_shuffle_options(f"{answer}°", [f"{d}°" for d in _distractors_around(int(answer), spread=40)]),
        correct_answer=f"{answer}°",
        explanation=explanation,
        difficulty=difficulty,
        topic="missing_angle",
    )


def _gen_regular_interior_angle(difficulty: int = 1) -> Problem:
    """Find each interior angle of a regular polygon."""
    sides = random.choice([5, 6, 8, 9, 10, 12] if difficulty >= 2 else [5, 6, 8])
    interior = (sides - 2) * 180 // sides
    name = POLYGON_NAMES.get(sides, f"{sides}-gon")

    svg = render_simple_polygon(sides, label=name)

    question = f"What is the measure of each interior angle of a regular {name.lower()}?"
    question_latex = (
        r"\text{What is the measure of each interior angle of a regular }"
        + name.lower()
        + "?"
    )
    explanation = (
        f"For a regular {name.lower()}, the sum of interior angles is $({sides} - 2) \\times 180^{{\\circ}} = {(sides - 2) * 180}^{{\\circ}}$. "
        f"Each interior angle is ${(sides - 2) * 180}^{{\\circ}} \\div {sides} = {interior}^{{\\circ}}$."
    )
    return Problem(
        question=question,
        question_latex=question_latex,
        svg_markup=svg,
        options=_shuffle_options(f"{interior}°", [f"{d}°" for d in _distractors_around(interior, spread=30)]),
        correct_answer=f"{interior}°",
        explanation=explanation,
        difficulty=difficulty,
        topic="regular_interior",
    )


def _gen_exterior_angle(difficulty: int = 1) -> Problem:
    """Find the exterior angle of a regular polygon."""
    sides = random.choice([5, 6, 8, 9, 10, 12] if difficulty >= 2 else [5, 6, 8])
    exterior = 360 // sides
    # Only pick values that divide evenly
    while 360 % sides != 0:
        sides = random.choice([5, 6, 8, 9, 10, 12])
        exterior = 360 // sides

    name = POLYGON_NAMES.get(sides, f"{sides}-gon")
    svg = render_simple_polygon(sides, label=name)

    question = f"What is the measure of each exterior angle of a regular {name.lower()}?"
    question_latex = (
        r"\text{What is the measure of each exterior angle of a regular }"
        + name.lower()
        + "?"
    )
    explanation = (
        f"The sum of exterior angles of any convex polygon is always $360^{{\\circ}}$. "
        f"For a regular {name.lower()} with {sides} sides, each exterior angle is $360^{{\\circ}} \\div {sides} = {exterior}^{{\\circ}}$."
    )
    return Problem(
        question=question,
        question_latex=question_latex,
        svg_markup=svg,
        options=_shuffle_options(f"{exterior}°", [f"{d}°" for d in _distractors_around(exterior, spread=25)]),
        correct_answer=f"{exterior}°",
        explanation=explanation,
        difficulty=difficulty,
        topic="exterior_angle",
    )


def _gen_angle_sum(difficulty: int = 2) -> Problem:
    """Find the sum of interior angles given number of sides, or vice versa."""
    if random.random() < 0.5:
        # Given sides, find sum
        sides = random.randint(5, 12)
        total = (sides - 2) * 180
        name = POLYGON_NAMES.get(sides, f"{sides}-gon")
        question = f"What is the sum of the interior angles of a {name.lower()}?"
        question_latex = (
            r"\text{What is the sum of the interior angles of a }"
            + name.lower()
            + "?"
        )
        svg = render_simple_polygon(sides)
        answer = f"{total}°"
        explanation = (
            f"The sum of interior angles of a polygon with $n$ sides is $(n - 2) \\times 180^{{\\circ}}$. "
            f"For a {name.lower()} ($n = {sides}$): $({sides} - 2) \\times 180^{{\\circ}} = {total}^{{\\circ}}$."
        )
        options = _shuffle_options(answer, [f"{d}°" for d in _distractors_around(total, spread=180)])
    else:
        # Given sum, find sides
        sides = random.randint(5, 12)
        total = (sides - 2) * 180
        question = f"A polygon has interior angles summing to {total}°. How many sides does it have?"
        question_latex = (
            r"\text{A polygon has interior angles summing to }"
            + str(total)
            + r"°. \text{ How many sides does it have?}"
        )
        svg = render_simple_polygon(sides)
        answer = str(sides)
        explanation = (
            f"Using $(n - 2) \\times 180^{{\\circ}} = {total}^{{\\circ}}$, we solve for $n$: "
            f"$n - 2 = {total // 180}$, so $n = {sides}$."
        )
        options = _shuffle_options(answer, _distractors_around(sides, spread=3))

    return Problem(
        question=question,
        question_latex=question_latex,
        svg_markup=svg,
        options=options,
        correct_answer=answer,
        explanation=explanation,
        difficulty=difficulty,
        topic="angle_sum",
    )


def _gen_name_from_angle_sum(difficulty: int = 2) -> Problem:
    """Given interior angle sum or regular angle, identify the polygon."""
    sides = random.randint(5, 12)
    total = (sides - 2) * 180
    name = POLYGON_NAMES.get(sides, f"{sides}-gon")

    if random.random() < 0.5:
        # From total sum
        question = f"Which polygon has interior angles that sum to {total}°?"
        question_latex = (
            r"\text{Which polygon has interior angles that sum to }"
            + str(total)
            + r"°?"
        )
        explanation = (
            f"Using $(n - 2) \\times 180^{{\\circ}} = {total}^{{\\circ}}$, we get $n = {sides}$. "
            f"A polygon with {sides} sides is a {name.lower()}."
        )
    else:
        # From regular interior angle
        interior = total // sides
        question = f"A regular polygon has interior angles of {interior}°. What is it?"
        question_latex = (
            r"\text{A regular polygon has interior angles of }"
            + str(interior)
            + r"°. \text{ What is it?}"
        )
        explanation = (
            f"Each interior angle is $(n - 2) \\times 180^{{\\circ}} / n = {interior}^{{\\circ}}$. "
            f"Solving gives $n = {sides}$, which is a {name.lower()}."
        )

    svg = render_simple_polygon(sides)
    all_names = [POLYGON_NAMES.get(n, f"{n}-gon") for n in range(3, 13)]
    options = _shuffle_options(name, _distractors_from_pool(name, all_names))

    return Problem(
        question=question,
        question_latex=question_latex,
        svg_markup=svg,
        options=options,
        correct_answer=name,
        explanation=explanation,
        difficulty=difficulty,
        topic="polygon_name",
    )


def _gen_sides_from_interior(difficulty: int = 3) -> Problem:
    """Given regular interior angle, find number of sides."""
    # Pick sides where interior angle is a nice integer
    candidates = [n for n in range(3, 13) if ((n - 2) * 180) % n == 0]
    sides = random.choice(candidates)
    interior = ((sides - 2) * 180) // sides
    name = POLYGON_NAMES.get(sides, f"{sides}-gon")

    question = f"A regular polygon has interior angles of {interior}°. How many sides does it have?"
    question_latex = (
        r"\text{A regular polygon has interior angles of }"
        + str(interior)
        + r"°. \text{ How many sides does it have?}"
    )
    svg = render_simple_polygon(sides)
    answer = str(sides)
    explanation = (
        f"Using the formula $(n - 2) \\times 180^{{\\circ}} / n = {interior}^{{\\circ}}$: "
        f"$(n - 2) \\times 180 = {interior}n$ → $180n - 360 = {interior}n$ → "
        f"${180 - interior}n = 360$ → $n = {sides}$."
    )

    return Problem(
        question=question,
        question_latex=question_latex,
        svg_markup=svg,
        options=_shuffle_options(answer, _distractors_around(sides, spread=3)),
        correct_answer=answer,
        explanation=explanation,
        difficulty=difficulty,
        topic="sides_from_angle",
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

_GENERATORS = [
    _gen_missing_triangle_angle,
    _gen_missing_quadrilateral_angle,
    _gen_regular_interior_angle,
    _gen_exterior_angle,
    _gen_angle_sum,
    _gen_name_from_angle_sum,
    _gen_sides_from_interior,
]


def generate_problem(
    difficulty: int = 1,
    topics: Optional[List[str]] = None,
) -> Problem:
    """Generate a random problem matching the criteria."""
    topics = topics or []
    eligible = _GENERATORS
    if topics:
        eligible = [g for g in _GENERATORS if hasattr(g, '__name__')]
        # Map function names to topics
        topic_map = {
            "missing_angle": [_gen_missing_triangle_angle, _gen_missing_quadrilateral_angle],
            "regular_interior": [_gen_regular_interior_angle],
            "exterior_angle": [_gen_exterior_angle],
            "angle_sum": [_gen_angle_sum],
            "polygon_name": [_gen_name_from_angle_sum],
            "sides_from_angle": [_gen_sides_from_interior],
        }
        eligible = []
        for t in topics:
            eligible.extend(topic_map.get(t, []))
        if not eligible:
            eligible = _GENERATORS

    gen = random.choice(eligible)
    # Cap difficulty to what generator supports
    prob = gen(difficulty=min(difficulty, 3))
    return prob


def generate_problem_set(count: int = 10, difficulty: int = 1, topics: Optional[List[str]] = None) -> List[Problem]:
    """Generate a set of unique-feeling problems."""
    problems = []
    for _ in range(count):
        p = generate_problem(difficulty=difficulty, topics=topics)
        problems.append(p)
    return problems
