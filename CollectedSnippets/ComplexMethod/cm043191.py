def process_element(element: element.PageElement) -> bool:
        try:
            if isinstance(element, NavigableString):
                if isinstance(element, Comment):
                    element.extract()
                return False

            if element.name in ["script", "style", "link", "meta", "noscript"]:
                element.decompose()
                return False

            keep_element = False

            if element.name == "a" and element.get("href"):
                href = element["href"]
                url_base = url.split("/")[2]
                link_data = {"href": href, "text": element.get_text()}
                if href.startswith("http") and url_base not in href:
                    links["external"].append(link_data)
                else:
                    links["internal"].append(link_data)
                keep_element = True

            elif element.name == "img":
                return True  # Always keep image elements

            elif element.name in ["video", "audio"]:
                media[f"{element.name}s"].append(
                    {
                        "src": element.get("src"),
                        "alt": element.get("alt"),
                        "type": element.name,
                        "description": find_closest_parent_with_useful_text(element),
                    }
                )
                source_tags = element.find_all("source")
                for source_tag in source_tags:
                    media[f"{element.name}s"].append(
                        {
                            "src": source_tag.get("src"),
                            "alt": element.get("alt"),
                            "type": element.name,
                            "description": find_closest_parent_with_useful_text(
                                element
                            ),
                        }
                    )
                return True  # Always keep video and audio elements

            if element.name != "pre":
                if element.name in [
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
                ]:
                    if kwargs.get("only_text", False):
                        element.replace_with(element.get_text())
                    else:
                        element.unwrap()
                elif element.name != "img":
                    element.attrs = {}

            # Process children
            for child in list(element.children):
                if isinstance(child, NavigableString) and not isinstance(
                    child, Comment
                ):
                    if len(child.strip()) > 0:
                        keep_element = True
                else:
                    if process_element(child):
                        keep_element = True

            # Check word count
            if not keep_element:
                word_count = len(element.get_text(strip=True).split())
                keep_element = word_count >= word_count_threshold

            if not keep_element:
                element.decompose()

            return keep_element
        except Exception as e:
            print("Error processing element:", str(e))
            return False