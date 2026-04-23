def create_messages(cls, messages: Messages, image_requests: ImageRequest = None, system_hints: list = None):
        """
        Create a list of messages for the user input

        Args:
            prompt: The user input as a string
            image_response: The image response object, if any

        Returns:
            A list of messages with the user input and the image, if any
        """
        # merged_messages = []
        # last_message = None
        # for message in messages:
        #     current_message = last_message
        #     if current_message is not None:
        #         if current_message["role"] == message["role"]:
        #             current_message["content"] += "\n" + message["content"]
        #         else:
        #             merged_messages.append(current_message)
        #             last_message = message.copy()
        #     else:
        #         last_message = message.copy()
        # if last_message is not None:
        #     merged_messages.append(last_message)

        messages = [{
            "id": str(uuid.uuid4()),
            "author": {"role": message["role"]},
            "content": {"content_type": "text", "parts": [to_string(message["content"])]},
            "metadata": {"serialization_metadata": {"custom_symbol_offsets": []},
                         **({"system_hints": system_hints} if system_hints else {})},
            "create_time": time.time(),
        } for message in messages]
        # Check if there is an image response
        if image_requests:
            # Change content in last user message
            messages[-1]["content"] = {
                "content_type": "multimodal_text",
                "parts": [*[{
                    "asset_pointer": f"file-service://{image_request.get('file_id')}",
                    "height": image_request.get("height"),
                    "size_bytes": image_request.get("file_size"),
                    "width": image_request.get("width"),
                }
                    for image_request in image_requests
                    # Add For Images Only
                    if image_request.get("use_case") == "multimodal"
                ],
                          messages[-1]["content"]["parts"][0]]
            }
            # Add the metadata object with the attachments
            messages[-1]["metadata"] = {
                "attachments": [{
                    "id": image_request.get("file_id"),
                    "mimeType": image_request.get("mime_type"),
                    "name": image_request.get("file_name"),
                    "size": image_request.get("file_size"),
                    **(
                        {
                            "height": image_request.get("height"),
                            "width": image_request.get("width"),
                        }
                        if image_request.get("use_case") == "multimodal"
                        else {}
                    ),
                }
                    for image_request in image_requests]
            }
        return messages