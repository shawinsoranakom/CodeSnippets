def _iter_blocks() -> Iterator[types.ContentBlock]:
        blocks: list[dict[str, Any]] = [
            cast("dict[str, Any]", block)
            if block.get("type") != "non_standard"
            else block["value"]  # type: ignore[typeddict-item]  # this is only non-standard blocks
            for block in content
        ]
        for block in blocks:
            num_keys = len(block)

            if num_keys == 1 and (text := block.get("text")):
                yield {"type": "text", "text": text}

            elif (
                num_keys == 1
                and (document := block.get("document"))
                and isinstance(document, dict)
                and "format" in document
            ):
                if document.get("format") == "pdf":
                    if "bytes" in document.get("source", {}):
                        file_block: types.FileContentBlock = {
                            "type": "file",
                            "base64": _bytes_to_b64_str(document["source"]["bytes"]),
                            "mime_type": "application/pdf",
                        }
                        _populate_extras(file_block, document, {"format", "source"})
                        yield file_block

                    else:
                        yield {"type": "non_standard", "value": block}

                elif document["format"] == "txt":
                    if "text" in document.get("source", {}):
                        plain_text_block: types.PlainTextContentBlock = {
                            "type": "text-plain",
                            "text": document["source"]["text"],
                            "mime_type": "text/plain",
                        }
                        _populate_extras(
                            plain_text_block, document, {"format", "source"}
                        )
                        yield plain_text_block
                    else:
                        yield {"type": "non_standard", "value": block}

                else:
                    yield {"type": "non_standard", "value": block}

            elif (
                num_keys == 1
                and (image := block.get("image"))
                and isinstance(image, dict)
                and "format" in image
            ):
                if "bytes" in image.get("source", {}):
                    image_block: types.ImageContentBlock = {
                        "type": "image",
                        "base64": _bytes_to_b64_str(image["source"]["bytes"]),
                        "mime_type": f"image/{image['format']}",
                    }
                    _populate_extras(image_block, image, {"format", "source"})
                    yield image_block

                else:
                    yield {"type": "non_standard", "value": block}

            elif block.get("type") in types.KNOWN_BLOCK_TYPES:
                yield cast("types.ContentBlock", block)

            else:
                yield {"type": "non_standard", "value": block}