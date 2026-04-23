def _process_chat_component(self):
        """Process the chat component and return the message.

        This method processes the chat component by extracting the necessary parameters
        such as sender, sender_name, and message from the `params` dictionary. It then
        performs additional operations based on the type of the `built_object` attribute.
        If `built_object` is an instance of `AIMessage`, it creates a `ChatOutputResponse`
        object using the `from_message` method. If `built_object` is not an instance of
        `UnbuiltObject`, it checks the type of `built_object` and performs specific
        operations accordingly. If `built_object` is a dictionary, it converts it into a
        code block. If `built_object` is an instance of `Data`, it assigns the `text`
        attribute to the `message` variable. If `message` is an instance of `AsyncIterator`
        or `Iterator`, it builds a stream URL and sets `message` to an empty string. If
        `built_object` is not a string, it converts it to a string. If `message` is a
        generator or iterator, it assigns it to the `message` variable. Finally, it creates
        a `ChatOutputResponse` object using the extracted parameters and assigns it to the
        `artifacts` attribute. If `artifacts` is not None, it calls the `model_dump` method
        on it and assigns the result to the `artifacts` attribute. It then returns the
        `message` variable.

        Returns:
            str: The processed message.
        """
        artifacts = None
        sender = self.params.get("sender", None)
        sender_name = self.params.get("sender_name", None)
        message = self.params.get(INPUT_FIELD_NAME, None)
        files = self.params.get("files", [])
        treat_file_path = files is not None and not isinstance(files, list) and isinstance(files, str)
        if treat_file_path:
            self.params["files"] = rewrite_file_path(files)
        files = [{"path": file} if isinstance(file, str) else file for file in self.params.get("files", [])]
        if isinstance(message, str):
            message = unescape_string(message)
        stream_url = None
        if "text" in self.results:
            text_output = self.results["text"]
        elif "message" in self.results:
            text_output = self.results["message"].text
        else:
            text_output = message
        if isinstance(text_output, AIMessage | AIMessageChunk):
            artifacts = ChatOutputResponse.from_message(
                text_output,
                sender=sender,
                sender_name=sender_name,
            )
        elif not isinstance(text_output, UnbuiltObject):
            if isinstance(text_output, dict):
                # Turn the dict into a pleasing to
                # read JSON inside a code block
                message = dict_to_codeblock(text_output)
            elif isinstance(text_output, Data):
                message = text_output.text
            elif isinstance(message, AsyncIterator | Iterator):
                stream_url = self.build_stream_url()
                message = ""
                self.results["text"] = message
                self.results["message"].text = message
                self.built_object = self.results
            elif not isinstance(text_output, str):
                message = str(text_output)
            # if the message is a generator or iterator
            # it means that it is a stream of messages

            else:
                message = text_output

            if hasattr(sender_name, "get_text"):
                sender_name = sender_name.get_text()

            artifact_type = ArtifactType.STREAM if stream_url is not None else ArtifactType.OBJECT
            artifacts = ChatOutputResponse(
                message=message,
                sender=sender,
                sender_name=sender_name,
                stream_url=stream_url,
                files=files,
                type=artifact_type,
            )

            self.will_stream = stream_url is not None
        if artifacts:
            self.artifacts = artifacts.model_dump(exclude_none=True)

        return message