def minify_files(html: bool = True, css: bool = True, js: bool = True):
    """Minify HTML, CSS, and JS files and print total reduction stats."""
    minify, compress, jsmin = None, None, None
    try:
        if html:
            from minify_html import minify
        if css:
            from csscompressor import compress
        if js:
            import jsmin
    except ImportError as e:
        LOGGER.info(f"Missing required package: {e}")
        return

    stats = {}
    for ext, minifier in {
        "html": (lambda x: minify(x, keep_closing_tags=True, minify_css=True, minify_js=True)) if html else None,
        "css": compress if css else None,
        "js": jsmin.jsmin if js else None,
    }.items():
        orig = minified = 0
        files = list(SITE.rglob(f"*.{ext}"))
        if not files:
            continue
        pbar = TQDM(files, desc=f"Minifying {ext.upper()} - reduced 0.00% (0.00 KB saved)")
        for f in pbar:
            content = f.read_text(encoding="utf-8")
            out = minifier(content) if minifier else remove_comments_and_empty_lines(content, ext)
            orig += len(content)
            minified += len(out)
            f.write_text(out, encoding="utf-8")
            saved = orig - minified
            pct = (saved / orig) * 100 if orig else 0.0
            pbar.set_description(f"Minifying {ext.upper()} - reduced {pct:.2f}% ({saved / 1024:.2f} KB saved)")
        stats[ext] = {"original": orig, "minified": minified}