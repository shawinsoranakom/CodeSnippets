def _maybe_adapt_message(message: dict[str, Any]) -> None:
            """Adapt message to `mistral-common` format and leave validation to `mistral-common`."""
            if not isinstance(message, dict):
                return message
            maybe_list_content: str | list[dict[str, str | dict[str, Any]]] | None = message.get("content")
            if not maybe_list_content or isinstance(maybe_list_content, str):
                return message

            normalized_content: list[dict[str, str | dict[str, Any]]] = []
            message = message.copy()
            for content in maybe_list_content:
                content_type = content.get("type", None)
                if not content_type:
                    continue
                elif content_type == "image":
                    maybe_url: str | None = content.get("url")
                    maybe_path: str | None = content.get("path")
                    maybe_base64: str | None = content.get("base64")
                    if maybe_url:
                        image_content = maybe_url
                    elif maybe_path:
                        if not maybe_path.startswith("file://"):
                            maybe_path = Path(maybe_path).resolve().as_uri()
                        image_content = maybe_path
                    elif maybe_base64:
                        if not maybe_base64.startswith("data:image"):
                            maybe_base64 = "data:image/unk;base64," + maybe_base64
                        image_content = maybe_base64
                    else:
                        raise ValueError("Image content must be specified.")
                    normalized_content.append({"type": "image_url", "image_url": {"url": image_content}})
                elif content_type == "audio":
                    maybe_url: str | None = content.get("url")
                    maybe_path: str | None = content.get("path")
                    maybe_base64: str | None = content.get("base64")
                    if maybe_url or maybe_path:
                        audio_data = load_audio_as(maybe_url or maybe_path, return_format="dict", force_mono=True)
                        normalized_content.append({"type": "input_audio", "input_audio": audio_data})
                        continue
                    if not maybe_base64:
                        raise ValueError("Audio content must be specified.")
                    normalized_content.append({"type": "audio_url", "audio_url": {"url": maybe_base64}})
                else:
                    normalized_content.append(content)
            message["content"] = normalized_content
            return message