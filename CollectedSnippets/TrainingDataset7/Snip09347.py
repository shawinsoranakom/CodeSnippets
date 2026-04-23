def compile_json_path(self, key_transforms, include_root=True):
        """
        Hook for backends to customize all aspects of JSON path construction.
        """
        path = ["$"] if include_root else []
        for key_transform in key_transforms:
            try:
                num = int(key_transform)
            except ValueError:  # Non-integer.
                path.append(".")
                path.append(json.dumps(key_transform))
            else:
                if (
                    num < 0
                    and not self.connection.features.supports_json_negative_indexing
                ):
                    raise NotSupportedError(
                        "Using negative JSON array indices is not supported on this "
                        "database backend."
                    )
                path.append(self.format_json_path_numeric_index(num))
        return "".join(path)