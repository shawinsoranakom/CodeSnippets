async def download_urls(
    bucket_dir: Path,
    urls: list[str],
    max_depth: int = 0,
    loading_urls: set[str] = set(),
    lock: asyncio.Lock = None,
    delay: int = 3,
    new_urls: list[str] = list(),
    group_size: int = 5,
    timeout: int = 10,
    proxy: Optional[str] = None
) -> AsyncIterator[str]:
    if lock is None:
        lock = asyncio.Lock()
    md = MarkItDown()
    async with ClientSession(
        connector=get_connector(proxy=proxy),
        timeout=ClientTimeout(timeout)
    ) as session:
        async def download_url(url: str, max_depth: int) -> str:
            text_content = None
            if has_markitdown:
                try:
                    text_content = md.convert_url(url).text_content
                    if text_content:
                        filename = get_filename_from_url(url)
                        target = bucket_dir / filename
                        text_content = f"{text_content.strip()}\n\nSource: {url}\n"
                        target.write_text(text_content, errors="replace")
                        return filename
                except Exception as e:
                    debug.log(f"Failed to convert URL to text: {type(e).__name__}: {e}")
            try:
                async with session.get(url) as response:
                    response.raise_for_status()
                    filename = await get_filename(response)
                    if not filename:
                        debug.log(f"Failed to get filename for {url}")
                        return None
                    if not is_allowed_extension(filename) and not supports_filename(filename) or filename == DOWNLOADS_FILE:
                        return None
                    if filename.endswith(".html") and max_depth > 0:
                        add_urls = read_links(await response.text(), str(response.url))
                        if add_urls:
                            async with lock:
                                add_urls = [add_url for add_url in add_urls if add_url not in loading_urls]
                                [loading_urls.add(add_url) for add_url in add_urls]
                                [new_urls.append(add_url) for add_url in add_urls if add_url not in new_urls]
                    if is_allowed_extension(filename):
                        target = bucket_dir / "media" / filename
                        target.parent.mkdir(parents=True, exist_ok=True)
                    else:
                        target = bucket_dir / filename
                    with target.open("wb") as f:
                        async for chunk in response.content.iter_any():
                            if filename.endswith(".html") and b'<link rel="canonical"' not in chunk:
                                f.write(chunk.replace(b'</head>', f'<link rel="canonical" href="{response.url}">\n</head>'.encode()))
                            else:
                                f.write(chunk)
                    return filename
            except (ClientError, asyncio.TimeoutError) as e:
                debug.log(f"Download failed: {e.__class__.__name__}: {e}")
            return None
        for filename in await asyncio.gather(*[download_url(url, max_depth) for url in urls]):
            if filename:
                yield filename
            else:
                await asyncio.sleep(delay)
        while new_urls:
            next_urls = list()
            for i in range(0, len(new_urls), group_size):
                chunked_urls = new_urls[i:i + group_size]
                async for filename in download_urls(bucket_dir, chunked_urls, max_depth - 1, loading_urls, lock, delay + 1, next_urls):
                    yield filename
                await asyncio.sleep(delay)
            new_urls = next_urls