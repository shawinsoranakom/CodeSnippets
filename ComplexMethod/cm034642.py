async def _generate_image(
        cls,
        model: str,
        alias: str,
        prompt: str,
        media: MediaListType,
        proxy: str,
        aspect_ratio: str,
        width: int,
        height: int,
        seed: Optional[int],
        cache: bool,
        nologo: bool,
        private: bool,
        enhance: bool,
        safe: bool,
        transparent: bool,
        n: int,
        api_key: str,
        timeout: int = 120
    ) -> AsyncResult:
        if enhance is None:
            enhance = True if model == "flux" else False
        params = {
            "model": model,
            "nologo": str(nologo).lower(),
            "private": str(private).lower(),
            "enhance": str(enhance).lower(),
            "safe": str(safe).lower(),
        }
        if not model or model == "auto":
            del params["model"]
        if transparent:
            params["transparent"] = "true"
        image = [data for data, _ in media if isinstance(data, str) and data.startswith("http")] if media else []
        if image:
            params["image"] = ",".join(image)
        if alias in cls.video_models:
            params["aspectRatio"] = aspect_ratio
        elif model != "gptimage":
            params = use_aspect_ratio({
                "width": width,
                "height": height,
                **params
            }, "1:1" if aspect_ratio is None else aspect_ratio)
        query = "&".join(f"{k}={quote(str(v))}" for k, v in params.items() if v is not None)
        encoded_prompt = prompt.strip()
        if model == "gptimage" and aspect_ratio is not None:
            encoded_prompt = f"{encoded_prompt} aspect-ratio: {aspect_ratio}"
        encoded_prompt = quote_plus(encoded_prompt)[:4096 - len(cls.image_api_endpoint) - len(query) - 8].rstrip("%")
        if api_key and not api_key.startswith("g4f_") and not api_key.startswith("gfs_"):
            url = cls.gen_image_api_endpoint
        else:
            url = cls.image_api_endpoint
        url = url.format(f"{encoded_prompt}?{query}")

        def get_url_with_seed(i: int, seed: Optional[int] = None):
            if i == 0:
                if not cache and seed is None:
                    seed = random.randint(0, 2 ** 32)
            else:
                seed = random.randint(0, 2 ** 32)
            return f"{url}&seed={seed}" if seed else url

        headers = None
        if api_key:
            headers = {"authorization": f"Bearer {api_key}"}
        async with ClientSession(
            headers=DEFAULT_HEADERS,
            connector=get_connector(proxy=proxy),
            timeout=ClientTimeout(timeout)
        ) as session:
            responses = set()
            yield Reasoning(label=f"Generating {n} {('video' if alias in cls.video_models else 'image') + '' if n == 1 else 's'}")
            finished = 0
            start = time.time()

            async def get_image(responses: set, i: int, seed: Optional[int] = None):
                try:
                    async with session.get(get_url_with_seed(i, seed), allow_redirects=False,
                                           headers=headers) as response:
                        await raise_for_status(response)
                except Exception as e:
                    responses.add(e)
                    debug.error(f"Error fetching image:", e)
                if response.headers.get("x-error-type"):
                    responses.add(PreviewResponse(ImageResponse(str(response.url), prompt)))
                elif response.headers.get('content-type', '').startswith("image/"):
                    responses.add(ImageResponse(str(response.url), prompt, {"headers": headers}))
                elif response.headers.get('content-type', '').startswith("video/"):
                    responses.add(VideoResponse(str(response.url), prompt, {"headers": headers}))
                else:
                    responses.add(Exception(f"Unexpected content type: {response.headers.get('content-type')}"))

            tasks: list[asyncio.Task] = []
            for i in range(int(n)):
                tasks.append(asyncio.create_task(get_image(responses, i, seed)))
            while finished < n or len(responses) > 0:
                while len(responses) > 0:
                    item = responses.pop()
                    if isinstance(item, Exception):
                        if finished < 2:
                            yield Reasoning(status="")
                            for task in tasks:
                                task.cancel()
                            if cls.login_url in str(item):
                                raise MissingAuthError(item)
                            raise item
                        else:
                            finished += 1
                            yield Reasoning(
                                label=f"Image {finished}/{n} failed after {time.time() - start:.2f}s: {item}")
                    else:
                        finished += 1
                        yield Reasoning(label=f"Image {finished}/{n} generated in {time.time() - start:.2f}s")
                        yield item
                await asyncio.sleep(1)
            yield Reasoning(status="")
            await asyncio.gather(*tasks)