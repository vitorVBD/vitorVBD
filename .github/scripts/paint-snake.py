"""Put a real fill on every snake cell.

Platane writes colors as CSS variables. Without a leading #, or when GitHub
strips the style block, every square falls back to black. This adds a fill
attribute and repairs hex values that are missing the hash.
"""

import re
import sys
from pathlib import Path


def hash_color(value: str) -> str:
    color = value.strip()
    if re.fullmatch(r"[0-9A-Fa-f]{3,8}", color):
        return f"#{color}"
    return color


def paint(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    root = re.search(r":root\{([^}]*)\}", text)
    variables = {}
    if root:
        for name, value in re.findall(r"(--[a-z0-9]+):([^;}]+)", root.group(1)):
            variables[name] = hash_color(value)

        repaired = root.group(0)
        for name, value in variables.items():
            repaired = repaired.replace(f"{name}:{value.lstrip('#')}", f"{name}:{value}", 1)
            repaired = repaired.replace(f"{name}:{value}", f"{name}:{value}")
        # Rewrite the whole :root so every variable has a hash when it is hex.
        body = ";".join(f"{name}:{value}" for name, value in variables.items())
        text = text[: root.start()] + f":root{{{body}}}" + text[root.end() :]

    class_fill = {}
    for class_name, variable in re.findall(
        r"\.(?:c|u)\.([cu][0-9a-z]+)\{fill:var\((--[a-z0-9]+)\)",
        text,
    ):
        class_fill[class_name] = variables.get(variable, "#FF2D3A")

    empty = variables.get("--ce", "#2A1538")
    snake = variables.get("--cs", "#FFFFFF")

    def fill_for(classes: list[str]) -> str:
        if "s" in classes:
            return snake
        for name in classes:
            if name in class_fill:
                return class_fill[name]
        return empty

    def paint_rect(match: re.Match[str]) -> str:
        tag = match.group(0)
        classes = re.search(r'class="([^"]+)"', tag)
        fill = fill_for(classes.group(1).split() if classes else [])
        tag = re.sub(r'\sfill="[^"]*"', "", tag)
        return tag[:-2] + f' fill="{fill}"/>'

    text = re.sub(r"<rect\b[^>]*/>", paint_rect, text)
    path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    for argument in sys.argv[1:]:
        paint(Path(argument))
