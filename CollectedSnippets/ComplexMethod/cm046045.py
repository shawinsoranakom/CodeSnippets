def create_text_placeholder(
    size: tuple[int, int], lines: list[str]
) -> Image.Image:
    width = max(int(size[0]), 1)
    height = max(int(size[1]), 1)
    placeholder = Image.new("RGB", (width, height), (240, 240, 240))
    draw = ImageDraw.Draw(placeholder)

    border_width = max(1, min(width, height) // 80)
    draw.rectangle(
        (0, 0, width - 1, height - 1),
        outline=(190, 190, 190),
        width=border_width,
    )

    max_text_width = max(width - 16, 1)
    max_text_height = max(height - 16, 1)
    fallback_text = "WMF/EMF"
    text = "\n".join(line for line in lines if line)
    if not text:
        text = fallback_text

    font = None
    spacing = 4
    bbox = None
    for font_size in range(max(min(width, height) // 7, 10), 7, -1):
        font = _load_placeholder_font(font_size)
        spacing = max(2, font_size // 4)
        bbox = draw.multiline_textbbox(
            (0, 0), text, font=font, spacing=spacing, align="center"
        )
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        if text_width <= max_text_width and text_height <= max_text_height:
            break
    else:
        text = fallback_text
        font = _load_placeholder_font(max(min(width, height) // 5, 10))
        spacing = 2
        bbox = draw.multiline_textbbox(
            (0, 0), text, font=font, spacing=spacing, align="center"
        )

    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    origin = ((width - text_width) / 2, (height - text_height) / 2)
    draw.multiline_text(
        origin,
        text,
        fill=(90, 90, 90),
        font=font,
        spacing=spacing,
        align="center",
    )
    return placeholder