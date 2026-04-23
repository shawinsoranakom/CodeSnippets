def crawl(self) -> list[Data]:
        if self.params:
            parameters = self.params["data"]
        else:
            parameters = {
                "limit": self.limit or None,
                "depth": self.depth or None,
                "blacklist": self.blacklist or None,
                "whitelist": self.whitelist or None,
                "readability": self.readability,
                "request_timeout": self.request_timeout or None,
                "metadata": self.metadata,
                "return_format": "markdown",
            }

        app = Spider(api_key=self.spider_api_key)
        if self.mode == "scrape":
            parameters["limit"] = 1
            result = app.scrape_url(self.url, parameters)
        elif self.mode == "crawl":
            result = app.crawl_url(self.url, parameters)
        else:
            msg = f"Invalid mode: {self.mode}. Must be 'scrape' or 'crawl'."
            raise ValueError(msg)

        records = []

        for record in result:
            if self.metadata:
                records.append(
                    Data(
                        data={
                            "content": record["content"],
                            "url": record["url"],
                            "metadata": record["metadata"],
                        }
                    )
                )
            else:
                records.append(Data(data={"content": record["content"], "url": record["url"]}))
        return records