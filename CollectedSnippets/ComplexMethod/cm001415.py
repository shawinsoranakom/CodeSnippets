async def _read_webpage_with_retry(
        self,
        url: str,
        topics_of_interest: list[str],
        get_raw_content: bool,
        question: str,
    ) -> str:
        """Internal method with retry logic for read_webpage."""
        page = None
        try:
            page = await self._open_page(url)

            html = await page.content()
            text = self._extract_text(html)
            links = self._extract_links(html, url)

            return_literal_content = True
            summarized = False

            if not text:
                return f"Website did not contain any text.\n\nLinks: {links}"
            elif get_raw_content:
                # Truncate instead of rejecting large pages
                text = self._truncate_content(text)
                return text + (f"\n\nLinks: {links}" if links else "")
            else:
                text = await self.summarize_webpage(
                    text, question or None, topics_of_interest
                )
                return_literal_content = bool(question)
                summarized = True

            # Limit links to LINKS_TO_RETURN
            if len(links) > LINKS_TO_RETURN:
                links = links[:LINKS_TO_RETURN]

            text_fmt = f"'''{text}'''" if "\n" in text else f"'{text}'"
            links_fmt = "\n".join(f"- {link}" for link in links)
            return (
                f"Page content{' (summary)' if summarized else ''}:"
                if return_literal_content
                else "Answer gathered from webpage:"
            ) + f" {text_fmt}\n\nLinks:\n{links_fmt}"

        finally:
            if page:
                await page.close()