def format(
        self,
        **kwargs: Any,
    ) -> ImageURL:
        """Format the prompt with the inputs.

        Args:
            **kwargs: Any arguments to be passed to the prompt template.

        Returns:
            A formatted string.

        Raises:
            ValueError: If the url is not provided.
            ValueError: If the url is not a string.
            ValueError: If `'path'` is provided in the template or kwargs.

        Example:
            ```python
            prompt.format(variable1="foo")
            ```
        """
        formatted = {}
        for k, v in self.template.items():
            if isinstance(v, str):
                formatted[k] = DEFAULT_FORMATTER_MAPPING[self.template_format](
                    v, **kwargs
                )
            else:
                formatted[k] = v
        url = kwargs.get("url") or formatted.get("url")
        if kwargs.get("path") or formatted.get("path"):
            msg = (
                "Loading images from 'path' has been removed as of 0.3.15 for security "
                "reasons. Please specify images by 'url'."
            )
            raise ValueError(msg)
        detail = kwargs.get("detail") or formatted.get("detail")
        if not url:
            msg = "Must provide url."
            raise ValueError(msg)
        if not isinstance(url, str):
            msg = "url must be a string."
            raise ValueError(msg)  # noqa: TRY004
        output: ImageURL = {"url": url}
        if detail:
            # Don't check literal values here: let the API check them
            output["detail"] = cast("Literal['auto', 'low', 'high']", detail)
        return output