def _create_nested_dict(self, variables, value_format):
        flat_dict = {}
        for v in variables:
            if v.path in flat_dict:
                raise ValueError(
                    "The following variable path is found twice in the model: "
                    f"'{v.path}'. `get_state_tree()` can only be called when "
                    "all variable paths are unique. Make sure to give unique "
                    "names to your layers (and other objects)."
                )
            if value_format == "backend_tensor":
                flat_dict[v.path] = v.value
            elif value_format == "numpy_array":
                flat_dict[v.path] = v.numpy()
            else:
                raise ValueError(
                    "Invalid `value_format` argument. Expected one of "
                    "{'numpy_array', 'backend_tensor'}. Received: "
                    f"value_format={value_format}"
                )

        nested_dict = {}
        for path, value in flat_dict.items():
            parts = path.split("/")
            current_dict = nested_dict
            for part in parts[:-1]:
                if part not in current_dict:
                    current_dict[part] = {}
                current_dict = current_dict[part]
            current_dict[parts[-1]] = value

        return nested_dict