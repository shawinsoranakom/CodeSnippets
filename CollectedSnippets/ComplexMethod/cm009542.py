def get_input_schema(self, config: RunnableConfig | None = None) -> type[BaseModel]:
        """The Pydantic schema for the input to this `Runnable`.

        Args:
            config: The config to use.

        Returns:
            The input schema for this `Runnable`.

        """
        func = getattr(self, "func", None) or self.afunc

        if isinstance(func, itemgetter):
            # This is terrible, but afaict it's not possible to access _items
            # on itemgetter objects, so we have to parse the repr
            items = str(func).replace("operator.itemgetter(", "")[:-1].split(", ")
            if all(
                item[0] == "'" and item[-1] == "'" and item != "''" for item in items
            ):
                fields = {item[1:-1]: (Any, ...) for item in items}
                # It's a dict, lol
                return create_model_v2(self.get_name("Input"), field_definitions=fields)
            module = getattr(func, "__module__", None)
            return create_model_v2(
                self.get_name("Input"),
                root=list[Any],
                # To create the schema, we need to provide the module
                # where the underlying function is defined.
                # This allows pydantic to resolve type annotations appropriately.
                module_name=module,
            )

        if self.InputType != Any:
            return super().get_input_schema(config)

        if dict_keys := get_function_first_arg_dict_keys(func):
            return create_model_v2(
                self.get_name("Input"),
                field_definitions=dict.fromkeys(dict_keys, (Any, ...)),
            )

        return super().get_input_schema(config)