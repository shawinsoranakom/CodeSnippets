def execute_func(
        self,
        parsed_args: argparse.Namespace | None = None,
    ) -> Any:
        """
        Execute the original function with the parsed arguments.

        Args:
            parsed_args (Optional[argparse.Namespace], optional): The parsed arguments. Defaults to None.

        Returns:
            Any: The return value of the original function.

        """
        kwargs = self._unflatten_args(vars(parsed_args))
        kwargs = self._update_with_custom_types(kwargs)
        provider = kwargs.get("provider")
        provider_args: list = []
        if provider and provider in self.provider_parameters:
            provider_args = self.provider_parameters[provider]
        else:
            for args in self.provider_parameters.values():
                provider_args.extend(args)

        # remove kwargs not matching the signature, provider parameters, or are empty.
        kwargs = {
            key: value
            for key, value in kwargs.items()
            if (
                (key in self.signature.parameters or key in provider_args)
                and (value or value is False)
            )
        }
        return self.func(**kwargs)