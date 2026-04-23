def perform_rss_read(self) -> DataFrame:
        """Read RSS feed."""
        rss_url = getattr(self, "query", "")
        if not rss_url:
            return DataFrame(
                pd.DataFrame([{"title": "Error", "link": "", "published": "", "summary": "No RSS URL provided"}])
            )

        try:
            response = requests.get(rss_url, timeout=self.timeout)
            response.raise_for_status()
            if not response.content.strip():
                msg = "Empty response received"
                raise ValueError(msg)

            # Validate XML
            try:
                BeautifulSoup(response.content, "xml")
            except Exception as e:
                msg = f"Invalid XML response: {e}"
                raise ValueError(msg) from e

            soup = BeautifulSoup(response.content, "xml")
            items = soup.find_all("item")
        except (requests.RequestException, ValueError) as e:
            self.status = f"Failed to fetch RSS: {e}"
            return DataFrame(pd.DataFrame([{"title": "Error", "link": "", "published": "", "summary": str(e)}]))

        articles = [
            {
                "title": item.title.text if item.title else "",
                "link": item.link.text if item.link else "",
                "published": item.pubDate.text if item.pubDate else "",
                "summary": item.description.text if item.description else "",
            }
            for item in items
        ]

        # Ensure DataFrame has correct columns even if empty
        df_articles = pd.DataFrame(articles, columns=["title", "link", "published", "summary"])
        self.log(f"Fetched {len(df_articles)} articles.")
        return DataFrame(df_articles)