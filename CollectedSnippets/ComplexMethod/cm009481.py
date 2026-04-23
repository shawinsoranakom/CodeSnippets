def format(self, **kwargs: Any) -> str:
        """Format the prompt with the inputs.

        Args:
            **kwargs: Any arguments to be passed to the prompt template.

        Returns:
            A formatted string.

        Example:
            ```python
            prompt.format(variable1="foo")
            ```
        """
        kwargs = self._merge_partial_and_user_variables(**kwargs)
        # Get the examples to use.
        examples = self._get_examples(**kwargs)
        # Format the examples.
        example_strings = [
            self.example_prompt.format(**example) for example in examples
        ]
        # Create the overall prefix.
        if self.prefix is None:
            prefix = ""
        else:
            prefix_kwargs = {
                k: v for k, v in kwargs.items() if k in self.prefix.input_variables
            }
            for k in prefix_kwargs:
                kwargs.pop(k)
            prefix = self.prefix.format(**prefix_kwargs)

        # Create the overall suffix
        suffix_kwargs = {
            k: v for k, v in kwargs.items() if k in self.suffix.input_variables
        }
        for k in suffix_kwargs:
            kwargs.pop(k)
        suffix = self.suffix.format(
            **suffix_kwargs,
        )

        pieces = [prefix, *example_strings, suffix]
        template = self.example_separator.join([piece for piece in pieces if piece])
        # Format the template with the input variables.
        return DEFAULT_FORMATTER_MAPPING[self.template_format](template, **kwargs)