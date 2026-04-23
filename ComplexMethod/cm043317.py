def generate_markdown(
        self,
        input_html: str,
        base_url: str = "",
        html2text_options: Optional[Dict[str, Any]] = None,
        options: Optional[Dict[str, Any]] = None,
        content_filter: Optional[RelevantContentFilter] = None,
        citations: bool = True,
        **kwargs,
    ) -> MarkdownGenerationResult:
        """
        Generate markdown with citations from the provided input HTML.

        How it works:
        1. Generate raw markdown from the input HTML.
        2. Convert links to citations.
        3. Generate fit markdown if content filter is provided.
        4. Return MarkdownGenerationResult.

        Args:
            input_html (str): The HTML content to process (selected based on content_source).
            base_url (str): Base URL for URL joins.
            html2text_options (Optional[Dict[str, Any]]): HTML2Text options.
            options (Optional[Dict[str, Any]]): Additional options for markdown generation.
            content_filter (Optional[RelevantContentFilter]): Content filter for generating fit markdown.
            citations (bool): Whether to generate citations.

        Returns:
            MarkdownGenerationResult: Result containing raw markdown, fit markdown, fit HTML, and references markdown.
        """
        try:
            # Initialize HTML2Text with default options for better conversion
            h = CustomHTML2Text(baseurl=base_url)
            default_options = {
                "body_width": 0,  # Disable text wrapping
                "ignore_emphasis": False,
                "ignore_links": False,
                "ignore_images": False,
                "protect_links": False,
                "single_line_break": True,
                "mark_code": True,
                "escape_snob": False,
            }

            # Update with custom options if provided
            if html2text_options:
                default_options.update(html2text_options)
            elif options:
                default_options.update(options)
            elif self.options:
                default_options.update(self.options)

            h.update_params(**default_options)

            # Ensure we have valid input
            if not input_html:
                input_html = ""
            elif not isinstance(input_html, str):
                input_html = str(input_html)

            # Generate raw markdown
            try:
                raw_markdown = h.handle(input_html)
            except Exception as e:
                raw_markdown = f"Error converting HTML to markdown: {str(e)}"

            raw_markdown = raw_markdown.replace("    ```", "```")

            # Convert links to citations
            markdown_with_citations: str = raw_markdown
            references_markdown: str = ""
            if citations:
                try:
                    (
                        markdown_with_citations,
                        references_markdown,
                    ) = self.convert_links_to_citations(raw_markdown, base_url)
                except Exception as e:
                    markdown_with_citations = raw_markdown
                    references_markdown = f"Error generating citations: {str(e)}"

            # Generate fit markdown if content filter is provided
            fit_markdown: Optional[str] = ""
            filtered_html: Optional[str] = ""
            if content_filter or self.content_filter:
                try:
                    content_filter = content_filter or self.content_filter
                    filtered_html = content_filter.filter_content(input_html)
                    filtered_html = "\n".join(
                        "<div>{}</div>".format(s) for s in filtered_html
                    )
                    fit_markdown = h.handle(filtered_html)
                except Exception as e:
                    fit_markdown = f"Error generating fit markdown: {str(e)}"
                    filtered_html = ""

            return MarkdownGenerationResult(
                raw_markdown=raw_markdown or "",
                markdown_with_citations=markdown_with_citations or "",
                references_markdown=references_markdown or "",
                fit_markdown=fit_markdown or "",
                fit_html=filtered_html or "",
            )
        except Exception as e:
            # If anything fails, return empty strings with error message
            error_msg = f"Error in markdown generation: {str(e)}"
            return MarkdownGenerationResult(
                raw_markdown=error_msg,
                markdown_with_citations=error_msg,
                references_markdown="",
                fit_markdown="",
                fit_html="",
            )