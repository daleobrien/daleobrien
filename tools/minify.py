"""Copy site/ to dist/, squeezing the HTML: no indentation, blank lines or
full-line comments, and tight CSS. Only whitespace and comments are removed, so
the page behaves exactly as the readable source in site/.

    python3 tools/minify.py site dist
"""

import re
import shutil
import sys
from pathlib import Path


def squeeze_css(css: str) -> str:
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    css = re.sub(r"\s+", " ", css)
    css = re.sub(r"\s*([{}:;,>])\s*", r"\1", css)
    # Media queries need their spaces around "and", and selectors like "a:hover"
    # never had any, so only put back the one after a colon inside @media (...).
    css = re.sub(r"\((min|max)-(width|height):", r"(\1-\2:", css)
    return css.replace(";}", "}").strip()


def squeeze_js(js: str) -> str:
    lines = []
    for line in js.splitlines():
        line = line.strip()
        # Full-line comments only: a "//" later in a line may be inside a string or URL.
        if not line or line.startswith("//") or line.startswith("/*") or line.startswith("*"):
            continue
        lines.append(line)
    return "\n".join(lines)


def squeeze_html(html: str) -> str:
    html = re.sub(r"<style>(.*?)</style>", lambda m: "<style>" + squeeze_css(m.group(1)) + "</style>", html, flags=re.S)
    html = re.sub(r"<script>(.*?)</script>", lambda m: "<script>" + squeeze_js(m.group(1)) + "</script>", html, flags=re.S)
    html = re.sub(r"<!--.*?-->", "", html, flags=re.S)
    out = []
    in_script = False
    for line in html.splitlines():
        if "<script>" in line:
            in_script = True
        stripped = line.strip()
        if stripped:
            out.append(stripped)
        if "</script>" in line:
            in_script = False
    # Join markup lines without newlines, but keep script lines on their own lines.
    text = "\n".join(out)
    text = re.sub(r">\n<", "><", text)
    return text + "\n"


def main(src: str, dst: str) -> None:
    src_path, dst_path = Path(src), Path(dst)
    shutil.rmtree(dst_path, ignore_errors=True)
    shutil.copytree(src_path, dst_path)
    for page in dst_path.rglob("*.html"):
        before = page.stat().st_size
        page.write_text(squeeze_html(page.read_text()))
        print(f"{page}: {before} -> {page.stat().st_size} bytes")


if __name__ == "__main__":
    main(*sys.argv[1:3])
