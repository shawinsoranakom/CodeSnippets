def _convert_image_to_html(img, base_url: str = "") -> str:
    """Convert an img element to HTML with size preservation.

    Uses HTML <img> tag when size information is present to preserve
    consistent rendering of checkmarks and icons.
    """
    src = img.get("src", "")
    alt = img.get("alt", "Image")
    if not src:
        return ""

    # Resolve relative URLs
    if base_url and not str(src).startswith(("http://", "https://", "data:")):
        src = urljoin(base_url, str(src))

    # Check for size information in style attribute
    style = img.get("style", "")
    width = None
    height = None

    if style:
        # Parse width and height from style like "width:0.0950528in;height:0.0894847in"
        width_match = re.search(r"width:\s*([0-9.]+(?:in|px|em|pt|%))", style)
        height_match = re.search(r"height:\s*([0-9.]+(?:in|px|em|pt|%))", style)
        if width_match:
            width = width_match.group(1)
        if height_match:
            height = height_match.group(1)

    # Also check for explicit width/height attributes
    if not width and img.get("width"):
        width = img.get("width")
        if not any(c.isalpha() for c in str(width)):
            width = f"{width}px"
    if not height and img.get("height"):
        height = img.get("height")
        if not any(c.isalpha() for c in str(height)):
            height = f"{height}px"

    # If we have size info, use HTML img tag to preserve it
    if width or height:
        style_parts = []
        if width:
            style_parts.append(f"width:{width}")
        if height:
            style_parts.append(f"height:{height}")
        style_str = ";".join(style_parts)
        return f'<img src="{src}" alt="{alt}" style="{style_str}"/>'

    # No size info, use standard markdown
    return f"![{alt}]({src})"