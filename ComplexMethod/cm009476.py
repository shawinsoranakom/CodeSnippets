def format(self, **kwargs: Any) -> BaseMessage:
        """Format the prompt template.

        Args:
            **kwargs: Keyword arguments to use for formatting.

        Returns:
            Formatted message.
        """
        if isinstance(self.prompt, StringPromptTemplate):
            text = self.prompt.format(**kwargs)
            return self._msg_class(
                content=text, additional_kwargs=self.additional_kwargs
            )
        content: list = []
        for prompt in self.prompt:
            inputs = {var: kwargs[var] for var in prompt.input_variables}
            if isinstance(prompt, StringPromptTemplate):
                formatted_text: str = prompt.format(**inputs)
                if formatted_text != "":
                    content.append({"type": "text", "text": formatted_text})
            elif isinstance(prompt, ImagePromptTemplate):
                formatted_image: ImageURL = prompt.format(**inputs)
                content.append({"type": "image_url", "image_url": formatted_image})
            elif isinstance(prompt, DictPromptTemplate):
                formatted_dict: dict[str, Any] = prompt.format(**inputs)
                content.append(formatted_dict)
        return self._msg_class(
            content=content, additional_kwargs=self.additional_kwargs
        )