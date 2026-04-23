def extract_metadata(html, soup=None):
    """
    Extract optimized content, media, and links from website HTML.

    How it works:
    1. Similar to `get_content_of_website`, but optimized for performance.
    2. Filters and scores images for usefulness.
    3. Extracts contextual descriptions for media files.
    4. Handles excluded tags and CSS selectors.
    5. Cleans HTML and converts it to Markdown.

    Args:
        url (str): The website URL.
        html (str): The HTML content of the website.
        word_count_threshold (int): Minimum word count for content inclusion. Defaults to MIN_WORD_THRESHOLD.
        css_selector (Optional[str]): CSS selector to extract specific content. Defaults to None.
        **kwargs: Additional options for customization.

    Returns:
        Dict[str, Any]: Extracted content including Markdown, cleaned HTML, media, links, and metadata.
    """

    metadata = {}

    if not html and not soup:
        return {}

    if not soup:
        soup = BeautifulSoup(html, "lxml")

    head = soup.head
    if not head:
        return metadata

    # Title
    title_tag = head.find("title")
    metadata["title"] = (
        title_tag.string.strip() if title_tag and title_tag.string else None
    )

    # Meta description
    description_tag = head.find("meta", attrs={"name": "description"})
    metadata["description"] = (
        description_tag.get("content", "").strip() if description_tag else None
    )

    # Meta keywords
    keywords_tag = head.find("meta", attrs={"name": "keywords"})
    metadata["keywords"] = (
        keywords_tag.get("content", "").strip() if keywords_tag else None
    )

    # Meta author
    author_tag = head.find("meta", attrs={"name": "author"})
    metadata["author"] = author_tag.get("content", "").strip() if author_tag else None

    # Open Graph metadata
    og_tags = head.find_all("meta", attrs={"property": re.compile(r"^og:")})
    for tag in og_tags:
        property_name = tag.get("property", "").strip()
        content = tag.get("content", "").strip()
        if property_name and content:
            metadata[property_name] = content

    # Twitter Card metadata
    twitter_tags = head.find_all("meta", attrs={"name": re.compile(r"^twitter:")})
    for tag in twitter_tags:
        property_name = tag.get("name", "").strip()
        content = tag.get("content", "").strip()
        if property_name and content:
            metadata[property_name] = content

    # Article metadata
    article_tags = head.find_all("meta", attrs={"property": re.compile(r"^article:")})
    for tag in article_tags:
        property_name = tag.get("property", "").strip()
        content = tag.get("content", "").strip()
        if property_name and content:
            metadata[property_name] = content

    return metadata