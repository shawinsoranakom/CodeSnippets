def _print_weights_structure(
        self, weights_dict, indent=0, is_first=True, prefix="", inner_path=""
    ):
        for idx, (key, value) in enumerate(weights_dict.items()):
            inner_path = os.path.join(inner_path, key)
            is_last = idx == len(weights_dict) - 1
            if is_first:
                is_first = False
                connector = "> "
            elif is_last:
                connector = "└─ "
            else:
                connector = "├─ "

            if isinstance(value, dict):
                bold_key = summary_utils.bold_text(key)
                object_label = f"{prefix}{connector}{bold_key}"
                if inner_path in self.object_metadata:
                    metadata = self.object_metadata[inner_path]
                    if "name" in metadata:
                        name = metadata["name"]
                        object_label += f" ('{name}')"
                self.console.print(object_label)
                if is_last:
                    appended = "    "
                else:
                    appended = "│   "
                new_prefix = prefix + appended
                self._print_weights_structure(
                    value,
                    indent + 1,
                    is_first=is_first,
                    prefix=new_prefix,
                    inner_path=inner_path,
                )
            else:
                if hasattr(value, "shape"):
                    bold_key = summary_utils.bold_text(key)
                    self.console.print(
                        f"{prefix}{connector}{bold_key}:"
                        + f" shape={value.shape}, dtype={value.dtype}"
                    )
                else:
                    self.console.print(f"{prefix}{connector}{key}: {value}")