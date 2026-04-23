async def run(
        self, input_data: Input, *, credentials: APIKeyCredentials, **kwargs
    ) -> BlockOutput:
        app = FirecrawlApp(api_key=credentials.api_key.get_secret_value())

        scrape_result = app.scrape(
            input_data.url,
            formats=convert_to_format_options(input_data.formats),
            only_main_content=input_data.only_main_content,
            max_age=input_data.max_age,
            wait_for=input_data.wait_for,
        )
        yield "data", scrape_result

        for f in input_data.formats:
            if f == ScrapeFormat.MARKDOWN:
                yield "markdown", scrape_result.markdown
            elif f == ScrapeFormat.HTML:
                yield "html", scrape_result.html
            elif f == ScrapeFormat.RAW_HTML:
                yield "raw_html", scrape_result.raw_html
            elif f == ScrapeFormat.LINKS:
                yield "links", scrape_result.links
            elif f == ScrapeFormat.SCREENSHOT:
                yield "screenshot", scrape_result.screenshot
            elif f == ScrapeFormat.SCREENSHOT_FULL_PAGE:
                yield "screenshot_full_page", scrape_result.screenshot
            elif f == ScrapeFormat.CHANGE_TRACKING:
                yield "change_tracking", scrape_result.change_tracking
            elif f == ScrapeFormat.JSON:
                yield "json", scrape_result.json