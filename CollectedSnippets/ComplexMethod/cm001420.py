def fetch_webpage(
        self,
        url: str,
        output_format: Literal["text", "markdown", "xml"] = "markdown",
        include_links: bool = True,
        include_comments: bool = False,
    ) -> str:
        """
        Fetch a webpage and extract its main content.

        Uses trafilatura for intelligent content extraction - automatically
        removes navigation, ads, boilerplate, and extracts the main article text.

        Args:
            url: The URL to fetch
            output_format: Output format (text, markdown, xml)
            include_links: Whether to include links from the page
            include_comments: Whether to include comments section

        Returns:
            Extracted content with optional metadata and links
        """
        response = self._fetch_url(url)
        html = response.text

        # Extract main content using trafilatura
        extract_kwargs = {
            "include_comments": include_comments,
            "include_links": output_format == "markdown",
            "include_images": False,
            "include_tables": True,
            "no_fallback": False,
        }

        if output_format == "markdown":
            content = trafilatura.extract(
                html,
                output_format="markdown",
                **extract_kwargs,  # type: ignore[arg-type]
            )
        elif output_format == "xml":
            content = trafilatura.extract(
                html,
                output_format="xml",
                **extract_kwargs,  # type: ignore[arg-type]
            )
        else:
            content = trafilatura.extract(
                html, **extract_kwargs  # type: ignore[arg-type]
            )

        if not content:
            # Fallback to basic BeautifulSoup extraction
            soup = BeautifulSoup(html, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()
            content = soup.get_text(separator="\n", strip=True)
            if not content:
                return "Could not extract content from this page."

        # Build output
        output_parts = []

        # Add metadata
        if self.config.include_metadata:
            metadata = self._extract_metadata(html)
            if metadata:
                meta_lines = []
                if "title" in metadata:
                    meta_lines.append(f"**Title:** {metadata['title']}")
                if "description" in metadata:
                    meta_lines.append(f"**Description:** {metadata['description']}")
                if "author" in metadata:
                    meta_lines.append(f"**Author:** {metadata['author']}")
                if "published" in metadata:
                    meta_lines.append(f"**Published:** {metadata['published']}")
                if meta_lines:
                    output_parts.append("## Page Info\n" + "\n".join(meta_lines))

        # Add main content
        output_parts.append(f"## Content\n{content}")

        # Add links
        if include_links and self.config.extract_links:
            links = self._extract_links(html, url)
            if links:
                links_text = "\n".join(f"- {link}" for link in links)
                output_parts.append(f"## Links ({len(links)})\n{links_text}")

        return "\n\n".join(output_parts)