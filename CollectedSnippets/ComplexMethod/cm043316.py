def convert_links_to_citations(
        self, markdown: str, base_url: str = ""
    ) -> Tuple[str, str]:
        """
        Convert links in markdown to citations.

        How it works:
        1. Find all links in the markdown.
        2. Convert links to citations.
        3. Return converted markdown and references markdown.

        Note:
        This function uses a regex pattern to find links in markdown.

        Args:
            markdown (str): Markdown text.
            base_url (str): Base URL for URL joins.

        Returns:
            Tuple[str, str]: Converted markdown and references markdown.
        """
        link_map = {}
        url_cache = {}  # Cache for URL joins
        parts = []
        last_end = 0
        counter = 1

        for match in LINK_PATTERN.finditer(markdown):
            parts.append(markdown[last_end : match.start()])
            text, url, title = match.groups()

            # Use cached URL if available, otherwise compute and cache
            if base_url and not url.startswith(("http://", "https://", "mailto:")):
                if url not in url_cache:
                    url_cache[url] = fast_urljoin(base_url, url)
                url = url_cache[url]

            if url not in link_map:
                desc = []
                if title:
                    desc.append(title)
                if text and text != title:
                    desc.append(text)
                link_map[url] = (counter, ": " + " - ".join(desc) if desc else "")
                counter += 1

            num = link_map[url][0]
            parts.append(
                f"{text}⟨{num}⟩"
                if not match.group(0).startswith("!")
                else f"![{text}⟨{num}⟩]"
            )
            last_end = match.end()

        parts.append(markdown[last_end:])
        converted_text = "".join(parts)

        # Pre-build reference strings
        references = ["\n\n## References\n\n"]
        references.extend(
            f"⟨{num}⟩ {url}{desc}\n"
            for url, (num, desc) in sorted(link_map.items(), key=lambda x: x[1][0])
        )

        return converted_text, "".join(references)