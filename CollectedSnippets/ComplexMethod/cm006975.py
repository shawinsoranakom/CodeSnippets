def map(self) -> Data:
        try:
            from firecrawl import FirecrawlApp
        except ImportError as e:
            msg = "Could not import firecrawl integration package. Please install it with `pip install firecrawl-py`."
            raise ImportError(msg) from e

        # Validate URLs
        if not self.urls:
            msg = "URLs are required"
            raise ValueError(msg)

        # Split and validate URLs (handle both commas and newlines)
        urls = [url.strip() for url in self.urls.replace("\n", ",").split(",") if url.strip()]
        if not urls:
            msg = "No valid URLs provided"
            raise ValueError(msg)

        params = {
            "ignoreSitemap": self.ignore_sitemap,
            "sitemapOnly": self.sitemap_only,
            "includeSubdomains": self.include_subdomains,
        }

        app = FirecrawlApp(api_key=self.api_key)

        # Map all provided URLs and combine results
        combined_links = []
        for url in urls:
            result = app.map_url(url, params=params)
            if isinstance(result, dict) and "links" in result:
                combined_links.extend(result["links"])

        map_result = {"success": True, "links": combined_links}

        return Data(data=map_result)