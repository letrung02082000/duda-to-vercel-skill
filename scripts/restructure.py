#!/usr/bin/env python3
"""
Restructure a Duda export into a Next.js public/ directory.

Usage:
    python restructure.py <duda-export-dir> <nextjs-project-dir>

Example:
    python restructure.py ./tiger2 ./tiger2-vercel

Copies:
    Resources/ -> public/Resources/
    Scripts/   -> public/Scripts/
    Style/     -> public/Style/
    Pages/     -> public/_pages/   (renamed to avoid Next.js conflict)
    sitemap.xml -> public/sitemap.xml
"""

import shutil
import sys
from pathlib import Path


def restructure(src_dir: Path, dest_dir: Path) -> None:
    public_dir = dest_dir / "public"
    public_dir.mkdir(parents=True, exist_ok=True)

    copies = [
        ("Resources", "Resources"),
        ("Scripts", "Scripts"),
        ("Style", "Style"),
        ("Pages", "_pages"),  # Rename to avoid Next.js App Router conflict
    ]

    for src_name, dest_name in copies:
        src_path = src_dir / src_name
        dest_path = public_dir / dest_name
        if not src_path.exists():
            print(f"  SKIP {src_name}/ (not found)")
            continue
        if dest_path.exists():
            print(f"  REMOVE existing {dest_name}/")
            shutil.rmtree(dest_path)
        print(f"  COPY {src_name}/ -> public/{dest_name}/")
        shutil.copytree(src_path, dest_path)

    # Copy sitemap.xml if exists
    sitemap_src = src_dir / "sitemap.xml"
    if sitemap_src.exists():
        print("  COPY sitemap.xml -> public/sitemap.xml")
        shutil.copy2(sitemap_src, public_dir / "sitemap.xml")

    # Count results
    html_count = len(list(public_dir.rglob("*.html")))
    css_count = len(list(public_dir.rglob("*.css")))
    js_count = len(list(public_dir.rglob("*.js")))
    img_count = len(list((public_dir / "Resources" / "images").rglob("*"))) if (public_dir / "Resources" / "images").exists() else 0

    print(f"\nDone! Copied to {public_dir}")
    print(f"  HTML: {html_count}, CSS: {css_count}, JS: {js_count}, Images: {img_count}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)

    src = Path(sys.argv[1]).resolve()
    dest = Path(sys.argv[2]).resolve()

    if not src.exists():
        print(f"Error: source directory not found: {src}")
        sys.exit(1)

    print(f"Restructuring Duda export: {src}")
    print(f"Into Next.js project: {dest}\n")
    restructure(src, dest)
