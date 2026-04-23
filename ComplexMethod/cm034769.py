def scrape_text(html: str, max_words: Optional[int] = None, add_source: bool = True, count_images: int = 2) -> Iterator[str]:
    """
    Parses the provided HTML and yields text fragments.
    """
    soup = BeautifulSoup(html, "html.parser")
    for selector in [
        "main", ".main-content-wrapper", ".main-content", ".emt-container-inner",
        ".content-wrapper", "#content", "#mainContent",
    ]:
        selected = soup.select_one(selector)
        if selected:
            soup = selected
            break

    for remove_selector in [".c-globalDisclosure"]:
        unwanted = soup.select_one(remove_selector)
        if unwanted:
            unwanted.extract()

    image_selector = "img[alt][src^=http]:not([alt='']):not(.avatar):not([width])"
    image_link_selector = f"a:has({image_selector})"
    seen_texts = []

    for element in soup.select(f"h1, h2, h3, h4, h5, h6, p, pre, table:not(:has(p)), ul:not(:has(p)), {image_link_selector}"):
        if count_images > 0:
            image = element.select_one(image_selector)
            if image:
                title = str(element.get("title", element.text))
                if title:
                    yield f"!{format_link(image['src'], title)}\n"
                    if max_words is not None:
                        max_words -= 10
                    count_images -= 1
                continue

        for line in element.get_text(" ").splitlines():
            words = [word for word in line.split() if word]
            if not words:
                continue
            joined_line = " ".join(words)
            if joined_line in seen_texts:
                continue
            if max_words is not None:
                max_words -= len(words)
                if max_words <= 0:
                    break
            yield joined_line + "\n"
            seen_texts.append(joined_line)

    if add_source:
        canonical_link = soup.find("link", rel="canonical")
        if canonical_link and "href" in canonical_link.attrs:
            link = canonical_link["href"]
            domain = urlparse(link).netloc
            yield f"\nSource: [{domain}]({link})"