def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: str | Sequence[str] | None,
        option_string: str | None = None,
    ):
        if values is None:
            values = []
        if isinstance(values, str):
            raise TypeError("Expected values to be a list")

        lora_list: list[LoRAModulePath] = []
        for item in values:
            if item in [None, ""]:  # Skip if item is None or empty string
                continue
            if "=" in item and "," not in item:  # Old format: name=path
                name, path = item.split("=")
                lora_list.append(LoRAModulePath(name, path))
            else:  # Assume JSON format
                try:
                    lora_dict = json.loads(item)
                    lora = LoRAModulePath(**lora_dict)
                    lora_list.append(lora)
                except json.JSONDecodeError:
                    parser.error(f"Invalid JSON format for --lora-modules: {item}")
                except TypeError as e:
                    parser.error(
                        f"Invalid fields for --lora-modules: {item} - {str(e)}"
                    )
        setattr(namespace, self.dest, lora_list)