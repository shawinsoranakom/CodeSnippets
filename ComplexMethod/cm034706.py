async def get_generated_image(cls, session: StreamSession, auth_result: AuthResult, element: Union[dict, str],
                                  prompt: str = None, conversation_id: str = None,
                                  status: Optional[str] = None) -> ImagePreview | ImageResponse | None:
        download_urls = []
        is_sediment = False
        if prompt is None:
            try:
                prompt = element["metadata"]["dalle"]["prompt"]
            except KeyError:
                pass
        if "asset_pointer" in element:
            element = element["asset_pointer"]
        if isinstance(element, str) and element.startswith("file-service://"):
            element = element.split("file-service://", 1)[-1]
        elif isinstance(element, str) and element.startswith("sediment://"):
            is_sediment = True
            element = element.split("sediment://")[-1]
        else:
            raise RuntimeError(f"Invalid image element: {element}")
        if is_sediment:
            url = f"{cls.url}/backend-api/conversation/{conversation_id}/attachment/{element}/download"
        else:
            url = f"{cls.url}/backend-api/files/{element}/download"
        try:
            async with session.get(url, headers=auth_result.headers) as response:
                cls._update_request_args(auth_result, session)
                await raise_for_status(response)
                data = await response.json()
                download_url = data.get("download_url")
                if download_url is not None:
                    download_urls.append(download_url)
                    debug.log(f"OpenaiChat: Found image: {download_url}")
                else:
                    debug.log("OpenaiChat: No download URL found in response: ", data)
        except Exception as e:
            debug.error("OpenaiChat: Download image failed")
            debug.error(e)
        if download_urls:
            # status = None, finished_successfully
            if is_sediment and status != "finished_successfully":
                return ImagePreview(download_urls, prompt, {"status": status, "headers": auth_result.headers})
            else:
                return ImageResponse(download_urls, prompt, {"status": status, "headers": auth_result.headers})