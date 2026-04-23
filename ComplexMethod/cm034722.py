async def get_response(cls, prompt: str, search: bool = False) -> Optional[VideoResponse]:
        if prompt in cls.urls and cls.urls[prompt]:
            unique_list = list(set(cls.urls[prompt]))[:10]
            return VideoResponse(unique_list, prompt, {
                "headers": {"authorization": cls.headers.get("authorization")} if cls.headers.get("authorization") else {},
            })
        if search:
            async with ClientSession() as session:
                found_urls = []
                for skip in range(0, 9):
                    try:
                        async with session.get(SEARCH_URL + quote_plus(prompt) + f"?skip={skip}", timeout=ClientTimeout(total=10)) as response:
                            if response.ok:
                                found_urls.append(str(response.url))
                            else:
                                break
                    except Exception as e:
                        debug.error(f"Error fetching video URLs:", e)
                        break
                if found_urls:
                    return VideoResponse(found_urls, prompt)