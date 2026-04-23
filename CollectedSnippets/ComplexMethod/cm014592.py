def et_get_selected_kernels(self, op_name: str, kernel_key: list[str]) -> list[str]:
        """
        Return a list of kernel keys that cover the used ops
        """
        # If no kernel metadata, either it's implied by include_all_operators=True or the op is not used.
        if op_name not in self.et_kernel_metadata:
            return kernel_key if self.include_all_operators else []
        # Otherwise, only return the specific kernel keys.

        result_set = set()

        for model_kernel_keys in self.et_kernel_metadata[op_name]:
            key_found = False
            for key in kernel_key:
                # Don't compare the version for now
                if (
                    key != "default"
                    and key.split("/")[1] == model_kernel_keys.split("/")[1]
                ):
                    result_set.add(key)
                    key_found = True
                    break
            if not key_found:
                if "default" not in kernel_key:
                    raise Exception("Missing kernel for the model")  # noqa: TRY002
                else:
                    result_set.add("default")

        return list(result_set)