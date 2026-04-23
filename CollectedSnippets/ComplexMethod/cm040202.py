def _edit_object(self, edit_fn, source_name, target_name=None):
        if target_name is not None and "/" in target_name:
            raise ValueError(
                "Argument `target_name` should be a leaf name, "
                "not a full path name. "
                f"Received: target_name='{target_name}'"
            )
        if "/" in source_name:
            # It's a path
            elements = source_name.split("/")
            weights_dict = self.weights_dict
            for e in elements[:-1]:
                if e not in weights_dict:
                    raise ValueError(
                        f"Path '{source_name}' not found in model."
                    )
                weights_dict = weights_dict[e]
            if elements[-1] not in weights_dict:
                raise ValueError(f"Path '{source_name}' not found in model.")
            edit_fn(
                weights_dict, source_name=elements[-1], target_name=target_name
            )
        else:
            # Ensure unicity
            def count_occurences(d, name, count=0):
                for k in d:
                    if isinstance(d[k], dict):
                        count += count_occurences(d[k], name, count)
                if name in d:
                    count += 1
                return count

            occurrences = count_occurences(self.weights_dict, source_name)
            if occurrences > 1:
                raise ValueError(
                    f"Name '{source_name}' occurs more than once in the model; "
                    "try passing a complete path"
                )
            if occurrences == 0:
                raise ValueError(
                    f"Source name '{source_name}' does not appear in the "
                    "model. Use `editor.weights_summary()` "
                    "to list all objects."
                )

            def _edit(d):
                for k in d:
                    if isinstance(d[k], dict):
                        _edit(d[k])
                if source_name in d:
                    edit_fn(d, source_name=source_name, target_name=target_name)

            _edit(self.weights_dict)