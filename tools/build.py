"""Build site/ into dist/ for status.do.id.au.

- The faces are slimmed (no XML prolog or label, the stubble dots as one path,
  the head outline drawn once and reused) and get their content hash in the
  name, e.g. faces/awake.3f2a9c1e.svg.
- The page's CSS and script move to app.<hash>.css and app.<hash>.js, squeezed
  (whitespace and comments only), and the script learns the faces' hashed names.
- index.html keeps its name and links to those files.

Everything but index.html can then be cached for a year: a change makes a new
name. Usage: python3 tools/build.py site dist
"""

import hashlib
import json
import re
import shutil
import sys
from pathlib import Path


def digest(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()[:8]


def slim_svg(svg: str) -> str:
    svg = re.sub(r"<\?xml[^>]*\?>\s*", "", svg)
    svg = re.sub(r'\s(aria-label|role)="[^"]*"', "", svg)

    # Stubble: many filled circles of one size -> one path of round dots.
    def dots(m):
        circles = re.findall(r'<circle cx="([\d.]+)" cy="([\d.]+)" r="([\d.]+)"/>', m.group(1))
        r = float(circles[0][2])
        d = "".join(f"M{float(x):g} {float(y):g}h0" for x, y, _ in circles)
        return f'<path stroke-width="{2 * r:g}" d="{d}"/>'

    svg = re.sub(r'<g fill="#000" stroke="none">((?:<circle [^>]*/>)+)</g>', dots, svg)

    # Each face is its own document (an <img>), so its ids can be one letter.
    mask = re.search(r'<mask id="([^"]+)"', svg)
    if mask:
        svg = svg.replace(f'id="{mask.group(1)}"', 'id="m"').replace(f"url(#{mask.group(1)})", "url(#m)")

    # The head outline appears twice (inside the ear mask, then drawn): define it once.
    head = re.search(r'<path d="(M90\.5 [^"]+Z)" fill="#000"/>', svg)
    if mask and head:
        hid = "h"
        d = head.group(1)
        svg = svg.replace(head.group(0), f'<use href="#{hid}" fill="#000"/>', 1)
        svg = svg.replace(f'<path d="{d}"/>', f'<use href="#{hid}"/>', 1)
        svg = svg.replace("<mask ", f'<defs><path id="{hid}" d="{d}"/></defs><mask ', 1)

    svg = re.sub(r">\s+<", "><", svg)
    svg = re.sub(r"\s+", " ", svg)
    return svg.strip() + "\n"


def squeeze_css(css: str) -> str:
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    css = re.sub(r"\s+", " ", css)
    css = re.sub(r"\s*([{}:;,>])\s*", r"\1", css)
    return css.replace(";}", "}").strip() + "\n"


def squeeze_js(js: str) -> str:
    keep = []
    for line in js.splitlines():
        line = line.strip()
        # Full-line comments only: a "//" later in a line may be inside a string or URL.
        if line and not line.startswith(("//", "/*", "*")):
            keep.append(line)
    return "\n".join(keep) + "\n"


def write_hashed(dst: Path, stem: str, ext: str, text: str) -> str:
    name = f"{stem}.{digest(text)}.{ext}"
    (dst / name).parent.mkdir(parents=True, exist_ok=True)
    (dst / name).write_text(text)
    return name


def main(src: str, dst: str) -> None:
    src_path, dst_path = Path(src), Path(dst)
    shutil.rmtree(dst_path, ignore_errors=True)
    dst_path.mkdir(parents=True)

    faces = {}
    before = after = 0
    for svg_file in sorted((src_path / "faces").glob("*.svg")):
        text = svg_file.read_text()
        slim = slim_svg(text)
        before += len(text)
        after += len(slim)
        faces[svg_file.stem] = write_hashed(dst_path, f"faces/{svg_file.stem}", "svg", slim)
    print(f"faces: {before} -> {after} bytes")

    html = (src_path / "index.html").read_text()
    css = re.search(r"<style>(.*?)</style>", html, re.S).group(1)
    js = re.search(r"<script>(.*?)</script>", html, re.S).group(1)
    assert "const FACES = {};" in js, "the page script must declare `const FACES = {};`"
    js = js.replace("const FACES = {};", "const FACES = " + json.dumps(faces, separators=(",", ":")) + ";")

    css_name = write_hashed(dst_path, "app", "css", squeeze_css(css))
    js_name = write_hashed(dst_path, "app", "js", squeeze_js(js))
    html = re.sub(r"\s*<style>.*?</style>", f'<link rel="stylesheet" href="{css_name}" />', html, flags=re.S)
    html = re.sub(r"<script>.*?</script>", f'<script src="{js_name}"></script>', html, flags=re.S)
    # The first face, shown before the script runs.
    html = html.replace('src="faces/awake.svg"', f'src="{faces["awake"]}"')
    html = re.sub(r"<!--.*?-->", "", html, flags=re.S)
    html = "\n".join(line.strip() for line in html.splitlines() if line.strip())
    html = re.sub(r">\s+<", "><", html) + "\n"
    (dst_path / "index.html").write_text(html)
    for f in ["index.html", css_name, js_name]:
        print(f"{f}: {(dst_path / f).stat().st_size} bytes")


if __name__ == "__main__":
    main(*sys.argv[1:3])
