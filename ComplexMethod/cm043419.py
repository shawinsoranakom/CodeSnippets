def scrap(self, url: str, html: str, **params) -> ScrapingResult:
        """
        Scrap content from a PDF file.

        Args:
            url (str): The URL of the PDF file.
            html (str): The HTML content of the page.
            **params: Additional parameters.

        Returns:
            ScrapingResult: The scraped content.
        """
        # Download if URL or use local path
        pdf_path = self._get_pdf_path(url)
        try:
            # Process PDF
            # result = self.pdf_processor.process(Path(pdf_path))
            result = self.pdf_processor.process_batch(Path(pdf_path))

            # Combine page HTML
            cleaned_html = f"""
        <html>
            <head><meta name="pdf-pages" content="{len(result.pages)}"></head>
            <body>
                {''.join(f'<div class="pdf-page" data-page="{i+1}">{page.html}</div>'
                         for i, page in enumerate(result.pages))}
            </body>
        </html>
        """

            # Accumulate media and links with page numbers
            media = {"images": []}
            links = {"urls": []}

            for page in result.pages:
                # Add page number to each image
                for img in page.images:
                    img["page"] = page.page_number
                    media["images"].append(img)

                # Add page number to each link
                for link in page.links:
                    links["urls"].append({
                        "url": link,
                        "page": page.page_number
                    })

            return ScrapingResult(
                cleaned_html=cleaned_html,
                success=True,
                media=media,
                links=links,
                metadata=asdict(result.metadata)
            )
        finally:
            # Cleanup temp file if downloaded
            if url.startswith(("http://", "https://")):
                try:
                    Path(pdf_path).unlink(missing_ok=True)
                    if pdf_path in self._temp_files:
                        self._temp_files.remove(pdf_path)
                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"Failed to cleanup temp file {pdf_path}: {e}")