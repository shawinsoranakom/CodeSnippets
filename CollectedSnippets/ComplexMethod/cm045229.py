def _add_set_of_mark(
    screenshot: Image.Image, ROIs: Dict[str, InteractiveRegion]
) -> Tuple[Image.Image, List[str], List[str], List[str]]:
    visible_rects: List[str] = list()
    rects_above: List[str] = list()  # Scroll up to see
    rects_below: List[str] = list()  # Scroll down to see

    fnt = ImageFont.load_default(14)
    base = screenshot.convert("L").convert("RGBA")
    overlay = Image.new("RGBA", base.size)

    draw = ImageDraw.Draw(overlay)
    for r in ROIs:
        for rect in ROIs[r]["rects"]:
            # Empty rectangles
            if not rect:
                continue
            if rect["width"] * rect["height"] == 0:
                continue

            mid = ((rect["right"] + rect["left"]) / 2.0, (rect["top"] + rect["bottom"]) / 2.0)

            if 0 <= mid[0] and mid[0] < base.size[0]:
                if mid[1] < 0:
                    rects_above.append(r)
                elif mid[1] >= base.size[1]:
                    rects_below.append(r)
                else:
                    visible_rects.append(r)
                    _draw_roi(draw, int(r), fnt, rect)

    comp = Image.alpha_composite(base, overlay)
    overlay.close()
    return comp, visible_rects, rects_above, rects_below