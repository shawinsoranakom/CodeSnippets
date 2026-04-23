async def create_async_generator(
        cls,
        model: str,
        messages: Messages,
        prompt: str = None,
        proxy: str = None,
        timeout: int = 30,
        region: str = None,
        backend: str = None,
        max_results: int = 5,
        max_words: int = 2500,
        add_text: bool = True,
        **kwargs
    ) -> AsyncResult:
        if not has_requirements:
            raise MissingRequirementsError('Install "ddgs" and "beautifulsoup4" | pip install -U g4f[search]')

        prompt = format_media_prompt(messages, prompt)
        results: List[SearchResultEntry] = []

        # Use the new DDGS() context manager style
        with DDGSClient() as ddgs:
            for result in ddgs.text(
                prompt,
                region=region,
                safesearch="moderate",
                timelimit="y",
                max_results=max_results,
                backend=backend,
            ):
                if ".google." in result["href"]:
                    continue
                results.append(SearchResultEntry(
                    title=result["title"],
                    url=result["href"],
                    snippet=result["body"]
                ))

        if add_text:
            tasks = []
            async with ClientSession(timeout=ClientTimeout(timeout)) as session:
                for entry in results:
                    tasks.append(fetch_and_scrape(session, entry.url, int(max_words / (max_results - 1)), False, proxy=proxy))
                texts = await asyncio.gather(*tasks)

        formatted_results: List[SearchResultEntry] = []
        used_words = 0
        left_words = max_words
        for i, entry in enumerate(results):
            if add_text:
                entry.text = texts[i]
            left_words -= entry.title.count(" ") + 5
            if entry.text:
                left_words -= entry.text.count(" ")
            else:
                left_words -= entry.snippet.count(" ")
            if left_words < 0:
                break
            used_words = max_words - left_words
            formatted_results.append(entry)

        yield SearchResults(formatted_results, used_words)