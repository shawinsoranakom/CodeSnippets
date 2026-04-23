def _extract_metadata(self, html: str) -> dict[str, str]:
        """Extract metadata from HTML."""
        soup = BeautifulSoup(html, "html.parser")
        metadata = {}

        # Title
        title_tag = soup.find("title")
        if title_tag:
            metadata["title"] = title_tag.get_text(strip=True)

        # Meta description
        desc = soup.find("meta", attrs={"name": "description"})
        if isinstance(desc, Tag) and desc.get("content"):
            metadata["description"] = str(desc["content"])

        # Open Graph title/description
        og_title = soup.find("meta", attrs={"property": "og:title"})
        if isinstance(og_title, Tag) and og_title.get("content"):
            metadata["og_title"] = str(og_title["content"])

        og_desc = soup.find("meta", attrs={"property": "og:description"})
        if isinstance(og_desc, Tag) and og_desc.get("content"):
            metadata["og_description"] = str(og_desc["content"])

        # Author
        author = soup.find("meta", attrs={"name": "author"})
        if isinstance(author, Tag) and author.get("content"):
            metadata["author"] = str(author["content"])

        # Published date
        for attr in ["article:published_time", "datePublished", "date"]:
            date_tag = soup.find("meta", attrs={"property": attr}) or soup.find(
                "meta", attrs={"name": attr}
            )
            if isinstance(date_tag, Tag) and date_tag.get("content"):
                metadata["published"] = str(date_tag["content"])
                break

        return metadata