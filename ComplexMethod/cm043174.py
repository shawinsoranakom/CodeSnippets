def extract_metadata_using_lxml(html, doc=None):
    """
    Extract metadata from HTML using lxml for better performance.
    """
    metadata = {}

    if not html and doc is None:
        return {}

    if doc is None:
        try:
            doc = lxml.html.document_fromstring(html)
        except Exception:
            return {}

    # Use XPath to find head element
    head = doc.xpath("//head")
    if not head:
        return metadata

    head = head[0]

    # Title - using XPath
    # title = head.xpath(".//title/text()")
    # metadata["title"] = title[0].strip() if title else None

    # === Title Extraction - New Approach ===
    # Attempt to extract <title> using XPath
    title = head.xpath(".//title/text()")
    title = title[0] if title else None

    # Fallback: Use .find() in case XPath fails due to malformed HTML
    if not title:
        title_el = doc.find(".//title")
        title = title_el.text if title_el is not None else None

    # Final fallback: Use OpenGraph or Twitter title if <title> is missing or empty
    if not title:
        title_candidates = (
            doc.xpath("//meta[@property='og:title']/@content") or
            doc.xpath("//meta[@name='twitter:title']/@content")
        )
        title = title_candidates[0] if title_candidates else None

    # Strip and assign title
    metadata["title"] = title.strip() if title else None

    # Meta description - using XPath with multiple attribute conditions
    description = head.xpath('.//meta[@name="description"]/@content')
    metadata["description"] = description[0].strip() if description else None

    # Meta keywords
    keywords = head.xpath('.//meta[@name="keywords"]/@content')
    metadata["keywords"] = keywords[0].strip() if keywords else None

    # Meta author
    author = head.xpath('.//meta[@name="author"]/@content')
    metadata["author"] = author[0].strip() if author else None

    # Open Graph metadata - using starts-with() for performance
    og_tags = head.xpath('.//meta[starts-with(@property, "og:")]')
    for tag in og_tags:
        property_name = tag.get("property", "").strip()
        content = tag.get("content", "").strip()
        if property_name and content:
            metadata[property_name] = content

    # Twitter Card metadata
    twitter_tags = head.xpath('.//meta[starts-with(@name, "twitter:")]')
    for tag in twitter_tags:
        property_name = tag.get("name", "").strip()
        content = tag.get("content", "").strip()
        if property_name and content:
            metadata[property_name] = content

   # Article metadata
    article_tags = head.xpath('.//meta[starts-with(@property, "article:")]')
    for tag in article_tags:
        property_name = tag.get("property", "").strip()
        content = tag.get("content", "").strip()
        if property_name and content:
            metadata[property_name] = content

    return metadata