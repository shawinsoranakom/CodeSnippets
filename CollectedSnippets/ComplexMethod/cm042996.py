async def run_test(label, bc, rc):
    print(f"\n{'='*70}")
    print(f"TEST: {label}")
    print(f"{'='*70}")
    async with AsyncWebCrawler(config=bc) as crawler:
        result = await crawler.arun(URL, config=rc)

    html = result.html or ""
    cleaned = result.cleaned_html or ""
    md = ""
    if result.markdown and hasattr(result.markdown, "raw_markdown"):
        md = result.markdown.raw_markdown or ""

    print(f"  Success:      {result.success}")
    print(f"  Raw HTML:     {len(html):>8} chars")
    print(f"  Cleaned HTML: {len(cleaned):>8} chars")
    print(f"  Markdown:     {len(md):>8} chars")

    checks = {
        "Product title":               "HYDRAULIC CYLINDER" in md,
        "Part number (R900999011)":    "R900999011" in md,
        "Product description":         "mill type design" in md.lower(),
        "Feature: 6 types of mounting":"6 types of mounting" in md,
        "Feature: safety vent":        "safety vent" in md.lower(),
        "Product Description heading": "Product Description" in md,
        "Technical Specs heading":     "Technical Specs" in md,
        "Downloads heading":           "Downloads" in md,
        "Specs table: CDH1":           "CDH1" in md,
        "Specs table: 250 bar":        "250" in md,
    }
    print(f"\n  Content checks:")
    passes = sum(1 for v in checks.values() if v)
    for k, v in checks.items():
        print(f"    {'PASS' if v else 'FAIL'}  {k}")
    print(f"\n  Result: {passes}/{len(checks)} checks passed")

    # Show product content section
    for term in ["Product Description"]:
        idx = md.find(term)
        if idx >= 0:
            print(f"\n  --- Product content section ---")
            print(md[idx:idx+1500])
    return result