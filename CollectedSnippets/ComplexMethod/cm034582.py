def create_completion(
        self,
        model: str,
        messages: Messages,
        stream: bool = False,
        **kwargs
    ) -> CreateResult:
        """
        Creates a completion result, processing any image creation prompts found within the messages.

        Args:
            model (str): The model to use for creation.
            messages (Messages): The messages to process, which may contain image prompts.
            stream (bool, optional): Indicates whether to stream the results. Defaults to False.
            **kwargs: Additional keywordarguments for the provider.

        Yields:
            CreateResult: Yields chunks of the processed messages, including image data if applicable.

        Note:
            This method processes messages to detect image creation prompts. When such a prompt is found, 
            it calls the synchronous image creation function and includes the resulting image in the output.
        """
        messages.insert(0, {"role": "system", "content": self.system_message})
        buffer = ""
        for chunk in self.provider.create_completion(model, messages, stream, **kwargs):
            if isinstance(chunk, ImageResponse):
                yield chunk
            elif isinstance(chunk, str) and buffer or "<" in chunk:
                buffer += chunk
                if ">" in buffer:
                    match = re.search(r'<img data-prompt="(.*?)">', buffer)
                    if match:
                        placeholder, prompt = match.group(0), match.group(1)
                        start, append = buffer.split(placeholder, 1)
                        if start:
                            yield start
                        if self.include_placeholder:
                            yield placeholder
                        if debug.logging:
                            print(f"Create images with prompt: {prompt}")
                        yield from self.create_images(prompt)
                        if append:
                            yield append
                    else:
                        yield buffer
                    buffer = ""
            else:
                yield chunk