def _process_request(
    request: "ChatCompletionRequest",
) -> tuple[
    list[dict[str, str]],
    Optional[str],
    Optional[str],
    Optional[list["ImageInput"]],
    Optional[list["VideoInput"]],
    Optional[list["AudioInput"]],
]:
    if is_env_enabled("API_VERBOSE", "1"):
        logger.info_rank0(f"==== request ====\n{json.dumps(dictify(request), indent=2, ensure_ascii=False)}")

    if len(request.messages) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid length")

    if request.messages[0].role == Role.SYSTEM:
        content = request.messages.pop(0).content
        if isinstance(content, list):
            system = content[0].text if content else ""
        else:
            system = content
    else:
        system = None

    if len(request.messages) % 2 == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only supports u/a/u/a/u...")

    input_messages = []
    images, videos, audios = [], [], []
    for i, message in enumerate(request.messages):
        if i % 2 == 0 and message.role not in [Role.USER, Role.TOOL]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role")
        elif i % 2 == 1 and message.role not in [Role.ASSISTANT, Role.FUNCTION]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role")

        if message.role == Role.ASSISTANT and isinstance(message.tool_calls, list) and len(message.tool_calls):
            tool_calls = [
                {"name": tool_call.function.name, "arguments": tool_call.function.arguments}
                for tool_call in message.tool_calls
            ]
            content = json.dumps(tool_calls, ensure_ascii=False)
            input_messages.append({"role": ROLE_MAPPING[Role.FUNCTION], "content": content})
        elif isinstance(message.content, list):
            text_content = ""
            for input_item in message.content:
                if input_item.type == "text":
                    text_content += input_item.text
                elif input_item.type == "image_url":
                    text_content += IMAGE_PLACEHOLDER
                    image_url = input_item.image_url.url
                    if re.match(r"^data:image\/(png|jpg|jpeg|gif|bmp);base64,(.+)$", image_url):  # base64 image
                        image_stream = io.BytesIO(base64.b64decode(image_url.split(",", maxsplit=1)[1]))
                    elif os.path.isfile(image_url):  # local file
                        check_lfi_path(image_url)
                        image_stream = open(image_url, "rb")
                    else:  # web uri
                        check_ssrf_url(image_url)
                        image_stream = requests.get(image_url, stream=True).raw

                    images.append(Image.open(image_stream).convert("RGB"))
                elif input_item.type == "video_url":
                    text_content += VIDEO_PLACEHOLDER
                    video_url = input_item.video_url.url
                    if re.match(r"^data:video\/(mp4|mkv|avi|mov);base64,(.+)$", video_url):  # base64 video
                        video_stream = io.BytesIO(base64.b64decode(video_url.split(",", maxsplit=1)[1]))
                    elif os.path.isfile(video_url):  # local file
                        check_lfi_path(video_url)
                        video_stream = video_url
                    else:  # web uri
                        check_ssrf_url(video_url)
                        video_stream = requests.get(video_url, stream=True).raw

                    videos.append(video_stream)
                elif input_item.type == "audio_url":
                    text_content += AUDIO_PLACEHOLDER
                    audio_url = input_item.audio_url.url
                    if re.match(r"^data:audio\/(mpeg|mp3|wav|ogg);base64,(.+)$", audio_url):  # base64 audio
                        audio_stream = io.BytesIO(base64.b64decode(audio_url.split(",", maxsplit=1)[1]))
                    elif os.path.isfile(audio_url):  # local file
                        check_lfi_path(audio_url)
                        audio_stream = audio_url
                    else:  # web uri
                        check_ssrf_url(audio_url)
                        audio_stream = requests.get(audio_url, stream=True).raw

                    audios.append(audio_stream)
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid input type {input_item.type}."
                    )

            input_messages.append({"role": ROLE_MAPPING[message.role], "content": text_content})
        else:
            input_messages.append({"role": ROLE_MAPPING[message.role], "content": message.content})

    tool_list = request.tools
    if isinstance(tool_list, list) and len(tool_list):
        try:
            tools = json.dumps([dictify(tool.function) for tool in tool_list], ensure_ascii=False)
        except json.JSONDecodeError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid tools")
    else:
        tools = None

    return input_messages, system, tools, images or None, videos or None, audios or None