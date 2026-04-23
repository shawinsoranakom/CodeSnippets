def get_content_of_website(
    url, html, word_count_threshold=MIN_WORD_THRESHOLD, css_selector=None, **kwargs
):
    """
    Extract structured content, media, and links from website HTML.

    How it works:
    1. Parses the HTML content using BeautifulSoup.
    2. Extracts internal/external links and media (images, videos, audios).
    3. Cleans the content by removing unwanted tags and attributes.
    4. Converts cleaned HTML to Markdown.
    5. Collects metadata and returns the extracted information.

    Args:
        url (str): The website URL.
        html (str): The HTML content of the website.
        word_count_threshold (int): Minimum word count for content inclusion. Defaults to MIN_WORD_THRESHOLD.
        css_selector (Optional[str]): CSS selector to extract specific content. Defaults to None.

    Returns:
        Dict[str, Any]: Extracted content including Markdown, cleaned HTML, media, links, and metadata.
    """

    try:
        if not html:
            return None
        # Parse HTML content with BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")

        # Get the content within the <body> tag
        body = soup.body

        # If css_selector is provided, extract content based on the selector
        if css_selector:
            selected_elements = body.select(css_selector)
            if not selected_elements:
                raise InvalidCSSSelectorError(
                    f"Invalid CSS selector , No elements found for CSS selector: {css_selector}"
                )
            div_tag = soup.new_tag("div")
            for el in selected_elements:
                div_tag.append(el)
            body = div_tag

        links = {"internal": [], "external": []}

        # Extract all internal and external links
        for a in body.find_all("a", href=True):
            href = a["href"]
            url_base = url.split("/")[2]
            if href.startswith("http") and url_base not in href:
                links["external"].append({"href": href, "text": a.get_text()})
            else:
                links["internal"].append({"href": href, "text": a.get_text()})

        # Remove script, style, and other tags that don't carry useful content from body
        for tag in body.find_all(["script", "style", "link", "meta", "noscript"]):
            tag.decompose()

        # Remove all attributes from remaining tags in body, except for img tags
        for tag in body.find_all():
            if tag.name != "img":
                tag.attrs = {}

        # Extract all img tgas int0 [{src: '', alt: ''}]
        media = {"images": [], "videos": [], "audios": []}
        for img in body.find_all("img"):
            media["images"].append(
                {"src": img.get("src"), "alt": img.get("alt"), "type": "image"}
            )

        # Extract all video tags into [{src: '', alt: ''}]
        for video in body.find_all("video"):
            media["videos"].append(
                {"src": video.get("src"), "alt": video.get("alt"), "type": "video"}
            )

        # Extract all audio tags into [{src: '', alt: ''}]
        for audio in body.find_all("audio"):
            media["audios"].append(
                {"src": audio.get("src"), "alt": audio.get("alt"), "type": "audio"}
            )

        # Replace images with their alt text or remove them if no alt text is available
        for img in body.find_all("img"):
            alt_text = img.get("alt")
            if alt_text:
                img.replace_with(soup.new_string(alt_text))
            else:
                img.decompose()

        # Create a function that replace content of all"pre" tag with its inner text
        def replace_pre_tags_with_text(node):
            for child in node.find_all("pre"):
                # set child inner html to its text
                child.string = child.get_text()
            return node

        # Replace all "pre" tags with their inner text
        body = replace_pre_tags_with_text(body)

        # Replace inline tags with their text content
        body = replace_inline_tags(
            body,
            [
                "b",
                "i",
                "u",
                "span",
                "del",
                "ins",
                "sub",
                "sup",
                "strong",
                "em",
                "code",
                "kbd",
                "var",
                "s",
                "q",
                "abbr",
                "cite",
                "dfn",
                "time",
                "small",
                "mark",
            ],
            only_text=kwargs.get("only_text", False),
        )

        # Recursively remove empty elements, their parent elements, and elements with word count below threshold
        def remove_empty_and_low_word_count_elements(node, word_count_threshold):
            for child in node.contents:
                if isinstance(child, element.Tag):
                    remove_empty_and_low_word_count_elements(
                        child, word_count_threshold
                    )
                    word_count = len(child.get_text(strip=True).split())
                    if (
                        len(child.contents) == 0 and not child.get_text(strip=True)
                    ) or word_count < word_count_threshold:
                        child.decompose()
            return node

        body = remove_empty_and_low_word_count_elements(body, word_count_threshold)

        def remove_small_text_tags(
            body: Tag, word_count_threshold: int = MIN_WORD_THRESHOLD
        ):
            # We'll use a list to collect all tags that don't meet the word count requirement
            tags_to_remove = []

            # Traverse all tags in the body
            for tag in body.find_all(True):  # True here means all tags
                # Check if the tag contains text and if it's not just whitespace
                if tag.string and tag.string.strip():
                    # Split the text by spaces and count the words
                    word_count = len(tag.string.strip().split())
                    # If the word count is less than the threshold, mark the tag for removal
                    if word_count < word_count_threshold:
                        tags_to_remove.append(tag)

            # Remove all marked tags from the tree
            for tag in tags_to_remove:
                tag.decompose()  # or tag.extract() to remove and get the element

            return body

        # Remove small text tags
        body = remove_small_text_tags(body, word_count_threshold)

        def is_empty_or_whitespace(tag: Tag):
            if isinstance(tag, NavigableString):
                return not tag.strip()
            # Check if the tag itself is empty or all its children are empty/whitespace
            if not tag.contents:
                return True
            return all(is_empty_or_whitespace(child) for child in tag.contents)

        def remove_empty_tags(body: Tag):
            # Continue processing until no more changes are made
            changes = True
            while changes:
                changes = False
                # Collect all tags that are empty or contain only whitespace
                empty_tags = [
                    tag for tag in body.find_all(True) if is_empty_or_whitespace(tag)
                ]
                for tag in empty_tags:
                    # If a tag is empty, decompose it
                    tag.decompose()
                    changes = True  # Mark that a change was made

            return body

        # Remove empty tags
        body = remove_empty_tags(body)

        # Flatten nested elements with only one child of the same type
        def flatten_nested_elements(node):
            for child in node.contents:
                if isinstance(child, element.Tag):
                    flatten_nested_elements(child)
                    if (
                        len(child.contents) == 1
                        and child.contents[0].name == child.name
                    ):
                        # print('Flattening:', child.name)
                        child_content = child.contents[0]
                        child.replace_with(child_content)

            return node

        body = flatten_nested_elements(body)

        # Remove comments
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()

        # Remove consecutive empty newlines and replace multiple spaces with a single space
        cleaned_html = str(body).replace("\n\n", "\n").replace("  ", " ")

        # Sanitize the cleaned HTML content
        cleaned_html = sanitize_html(cleaned_html)
        # sanitized_html = escape_json_string(cleaned_html)

        # Convert cleaned HTML to Markdown
        h = html2text.HTML2Text()
        h = CustomHTML2Text()
        h.ignore_links = True
        markdown = h.handle(cleaned_html)
        markdown = markdown.replace("    ```", "```")

        try:
            meta = extract_metadata(html, soup)
        except Exception as e:
            print("Error extracting metadata:", str(e))
            meta = {}

        # Return the Markdown content
        return {
            "markdown": markdown,
            "cleaned_html": cleaned_html,
            "success": True,
            "media": media,
            "links": links,
            "metadata": meta,
        }

    except Exception as e:
        print("Error processing HTML content:", str(e))
        raise InvalidCSSSelectorError(f"Invalid CSS selector: {css_selector}") from e