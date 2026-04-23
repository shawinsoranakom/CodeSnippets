def split_html_by_headers(self, html_doc: str) -> list[dict[str, str | None]]:
        """Split an HTML document into sections based on specified header tags.

        This method uses BeautifulSoup to parse the HTML content and divides it into
        sections based on headers defined in `headers_to_split_on`. Each section
        contains the header text, content under the header, and the tag name.

        Args:
            html_doc: The HTML document to be split into sections.

        Returns:
            A list of dictionaries representing sections.

                Each dictionary contains:

                * `'header'`: The header text or a default title for the first section.
                * `'content'`: The content under the header.
                * `'tag_name'`: The name of the header tag (e.g., `h1`, `h2`).

        Raises:
            ImportError: If BeautifulSoup is not installed.
        """
        if not _HAS_BS4:
            msg = "Unable to import BeautifulSoup/PageElement, \
                    please install with `pip install \
                    bs4`."
            raise ImportError(msg)

        soup = BeautifulSoup(html_doc, "html.parser")
        header_names = list(self.headers_to_split_on.keys())
        sections: list[dict[str, str | None]] = []

        headers = _find_all_tags(soup, name=["body", *header_names])

        for i, header in enumerate(headers):
            if i == 0:
                current_header = "#TITLE#"
                current_header_tag = "h1"
                section_content: list[str] = []
            else:
                current_header = header.text.strip()
                current_header_tag = header.name
                section_content = []
            for element in header.next_elements:
                if i + 1 < len(headers) and element == headers[i + 1]:
                    break
                if isinstance(element, str):
                    section_content.append(element)
            content = " ".join(section_content).strip()

            if content:
                sections.append(
                    {
                        "header": current_header,
                        "content": content,
                        "tag_name": current_header_tag,
                    }
                )

        return sections