def normalize_url_tmp(href, base_url):
    """Normalize URLs to ensure consistent format"""
    # Extract protocol and domain from base URL
    try:
        base_parts = base_url.split("/")
        protocol = base_parts[0]
        domain = base_parts[2]
    except IndexError:
        raise ValueError(f"Invalid base URL format: {base_url}")

    # Handle special protocols
    special_protocols = {"mailto:", "tel:", "ftp:", "file:", "data:", "javascript:"}
    if any(href.lower().startswith(proto) for proto in special_protocols):
        return href.strip()

    # Handle anchor links
    if href.startswith("#"):
        return f"{base_url}{href}"

    # Handle protocol-relative URLs
    if href.startswith("//"):
        return f"{protocol}{href}"

    # Handle root-relative URLs
    if href.startswith("/"):
        return f"{protocol}//{domain}{href}"

    # Handle relative URLs
    if not href.startswith(("http://", "https://")):
        # Remove leading './' if present
        href = href.lstrip("./")
        return f"{protocol}//{domain}/{href}"

    return href.strip()