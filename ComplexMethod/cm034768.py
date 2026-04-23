async def create_async_generator(
        cls,
        model: str,
        messages: Messages,
        prompt: str = None,
        **kwargs
    ) -> AsyncResult:
        prompt = format_media_prompt(messages, prompt)
        results = [{
            "id": line.split("?v=")[-1].split("&")[0],
            "url": line
        } for line in prompt.splitlines()
            if line.startswith("https://www.youtube.com/watch?v=")]
        provider = YouTubeProvider()
        if not results:
            results = await provider.search(prompt, max_results=10)
        new_results = []
        for result in results:
            video_url = result['url']
            has_video = False
            for message in messages:
                if isinstance(message.get("content"), str):
                    if video_url in message["content"] and (model == "search" or model in message["content"]):
                        has_video = True
                        break
            if has_video:
                continue
            new_results.append(result)
        if model == "search":
            yield YouTubeResponse([result["id"] for result in new_results[:5]], True)
        else:
            if new_results:
                video_url = new_results[0]['url']
                path = await provider.download(video_url, model=model, output_dir=get_media_dir())
                if path.endswith('.mp3'):
                    yield AudioResponse(f"/media/{os.path.basename(path)}")
                else:
                    yield VideoResponse(f"/media/{os.path.basename(path)}", prompt)
                yield f"\n\n[{video_url}]({video_url})\n\n"