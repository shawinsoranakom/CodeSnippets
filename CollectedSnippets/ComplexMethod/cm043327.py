def extract_page_query(self, soup: BeautifulSoup, body: Tag) -> str:
        """Common method to extract page metadata with fallbacks"""
        if self.user_query:
            return self.user_query

        query_parts = []

        # Title
        try:
            title = soup.title.string
            if title:
                query_parts.append(title)
        except Exception:
            pass

        if soup.find("h1"):
            query_parts.append(soup.find("h1").get_text())

        # Meta tags
        temp = ""
        for meta_name in ["keywords", "description"]:
            meta = soup.find("meta", attrs={"name": meta_name})
            if meta and meta.get("content"):
                query_parts.append(meta["content"])
                temp += meta["content"]

        # If still empty, grab first significant paragraph
        if not temp:
            # Find the first tag P thatits text contains more than 50 characters
            for p in body.find_all("p"):
                if len(p.get_text()) > 150:
                    query_parts.append(p.get_text()[:150])
                    break

        return " ".join(filter(None, query_parts))