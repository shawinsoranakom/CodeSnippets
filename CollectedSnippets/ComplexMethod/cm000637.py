async def run(
        self, input_data: Input, *, credentials: APIKeyCredentials, **kwargs
    ) -> BlockOutput:
        app = FirecrawlApp(api_key=credentials.api_key.get_secret_value())

        # Sync call
        crawl_result = app.crawl(
            input_data.url,
            limit=input_data.limit,
            scrape_options=ScrapeOptions(
                formats=convert_to_format_options(input_data.formats),
                only_main_content=input_data.only_main_content,
                max_age=input_data.max_age,
                wait_for=input_data.wait_for,
            ),
        )
        yield "data", crawl_result.data

        for data in crawl_result.data:
            for f in input_data.formats:
                if f == ScrapeFormat.MARKDOWN:
                    yield "markdown", data.markdown
                elif f == ScrapeFormat.HTML:
                    yield "html", data.html
                elif f == ScrapeFormat.RAW_HTML:
                    yield "raw_html", data.raw_html
                elif f == ScrapeFormat.LINKS:
                    yield "links", data.links
                elif f == ScrapeFormat.SCREENSHOT:
                    yield "screenshot", data.screenshot
                elif f == ScrapeFormat.SCREENSHOT_FULL_PAGE:
                    yield "screenshot_full_page", data.screenshot
                elif f == ScrapeFormat.CHANGE_TRACKING:
                    yield "change_tracking", data.change_tracking
                elif f == ScrapeFormat.JSON:
                    yield "json", data.json