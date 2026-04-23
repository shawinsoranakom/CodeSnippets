def perform_news_search(self) -> DataFrame:
        """Perform Google News search."""
        query = getattr(self, "query", "")
        hl = getattr(self, "hl", "en-US") or "en-US"
        gl = getattr(self, "gl", "US") or "US"
        topic = getattr(self, "topic", None)
        location = getattr(self, "location", None)

        ceid = f"{gl}:{hl.split('-')[0]}"

        # Build RSS URL based on parameters
        if topic:
            # Topic-based feed
            base_url = f"https://news.google.com/rss/headlines/section/topic/{quote_plus(topic.upper())}"
            params = f"?hl={hl}&gl={gl}&ceid={ceid}"
            rss_url = base_url + params
        elif location:
            # Location-based feed
            base_url = f"https://news.google.com/rss/headlines/section/geo/{quote_plus(location)}"
            params = f"?hl={hl}&gl={gl}&ceid={ceid}"
            rss_url = base_url + params
        elif query:
            # Keyword search feed
            base_url = "https://news.google.com/rss/search?q="
            query_encoded = quote_plus(query)
            params = f"&hl={hl}&gl={gl}&ceid={ceid}"
            rss_url = f"{base_url}{query_encoded}{params}"
        else:
            self.status = "No search query, topic, or location provided."
            return DataFrame(
                pd.DataFrame(
                    [{"title": "Error", "link": "", "published": "", "summary": "No search parameters provided"}]
                )
            )

        try:
            response = requests.get(rss_url, timeout=self.timeout)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "xml")
            items = soup.find_all("item")
        except requests.RequestException as e:
            self.status = f"Failed to fetch news: {e}"
            return DataFrame(pd.DataFrame([{"title": "Error", "link": "", "published": "", "summary": str(e)}]))

        if not items:
            self.status = "No news articles found."
            return DataFrame(pd.DataFrame([{"title": "No articles found", "link": "", "published": "", "summary": ""}]))

        articles = []
        for item in items:
            try:
                title = self.clean_html(item.title.text if item.title else "")
                link = item.link.text if item.link else ""
                published = item.pubDate.text if item.pubDate else ""
                summary = self.clean_html(item.description.text if item.description else "")
                articles.append({"title": title, "link": link, "published": published, "summary": summary})
            except (AttributeError, ValueError, TypeError) as e:
                self.log(f"Error parsing article: {e!s}")
                continue

        return DataFrame(pd.DataFrame(articles))