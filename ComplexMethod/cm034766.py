async def create_async_generator(
        cls,
        model: str,
        messages: Messages,
        prompt: str = None,
        **kwargs
    ) -> AsyncResult:
        """
        Combines search results with the user prompt, using caching for improved efficiency.
        """
        prompt = format_media_prompt(messages, prompt)
        search_parameters = ["max_results", "max_words", "add_text", "timeout", "region"]
        search_parameters = {k: v for k, v in kwargs.items() if k in search_parameters}
        json_bytes = json.dumps({"model": model, "query": prompt, **search_parameters}, sort_keys=True).encode(errors="ignore")
        md5_hash = hashlib.md5(json_bytes).hexdigest()
        cache_dir: Path = Path(get_cookies_dir()) / ".scrape_cache" / "web_search" / f"{date.today()}"
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = cache_dir / f"{quote_plus(prompt[:20])}.{md5_hash}.cache"

        search_results: Optional[SearchResults] = None
        if cache_file.exists():
            with cache_file.open("r") as f:
                try:
                    search_results = SearchResults.from_dict(json.loads(f.read()))
                except json.JSONDecodeError:
                    search_results = None

        if search_results is None:
            if model:
                search_parameters["provider"] = model
            search_results = await search(prompt, **search_parameters)
            if search_results.results:
                with cache_file.open("w") as f:
                    f.write(json.dumps(search_results.get_dict()))

        yield search_results