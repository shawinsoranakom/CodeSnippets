async def _process_image_response(
        self,
        response: MediaResponse,
        model: str,
        provider: str,
        download_media: bool,
        response_format: Optional[str] = None,
        proxy: str = None
    ) -> ImagesResponse:
        if response_format == "url":
            # Return original URLs without saving locally
            images = [Image.model_construct(url=image, revised_prompt=response.alt) for image in response.get_list()]
        elif response_format == "b64_json":
            # Convert URLs directly to base64 without saving
            async def get_b64_from_url(url: str) -> Image:
                if url.startswith("/media/"):
                    with open(os.path.join(get_media_dir(), os.path.basename(url)), "rb") as f:
                        b64_data = base64.b64encode(f.read()).decode()
                        return Image.model_construct(b64_json=b64_data, revised_prompt=response.alt)
                async with aiohttp.ClientSession(cookies=response.get("cookies")) as session:
                    async with session.get(url, proxy=proxy) as resp:
                        if resp.status == 200:
                            b64_data = base64.b64encode(await resp.read()).decode()
                            return Image.model_construct(b64_json=b64_data, revised_prompt=response.alt)
                return Image.model_construct(url=url, revised_prompt=response.alt)
            images = await asyncio.gather(*[get_b64_from_url(image) for image in response.get_list()])
        else:
            # Save locally for None (default) case
            images = response.get_list()
            if download_media or response.get("cookies") or response.get("headers"):
                images = await copy_media(response.get_list(), response.get("cookies"), response.get("headers"), proxy, response.alt)
            images = [Image.model_construct(url=image, revised_prompt=response.alt) for image in images]

        return ImagesResponse.model_construct(
            created=int(time.time()),
            data=images,
            model=model,
            provider=provider
        )