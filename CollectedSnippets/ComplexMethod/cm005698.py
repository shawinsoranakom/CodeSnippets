def sanitize_kernel_mapping(self, model):
        """
        Validates the kernel_mapping to ensure that:
        1. Each layer_name in the mapping is registered in the model (i.e., the model contains a module with a matching kernel_layer_name).
        2. Each kernel value is either a string of the form 'org/repo:layer_name' or a dict mapping device types ("cuda", "rocm", "xpu", "npu") to such strings.
        3. Each device key in a dict is one of "cuda", "rocm", "xpu", or "npu".
        4. Each repo_name is a valid repository and layer name in the format 'org/repo:layer_name' (i.e., a string containing both a slash and a colon).
        5. If a local path is detected, it should be in the format '/abs/path:layer_name'. The absolute path must include the `package_name`, like "/home/user/layer_norm".

        Args:
            model: The model instance whose modules are checked for registered kernel_layer_name attributes.

        Raises:
            ValueError: If a layer_name is not registered in the model, if a device is not supported,
                        or if a repo_name is not a valid 'org/repo:layer_name' string.
        """
        MAPPING_FORMAT = """
        For single device form remote
        {
            "RMSNorm":
                "kernels-community/layer_norm:LlamaRMSNorm",
            ...
        },
        For multiple devices form remote
        {
            "RMSNorm": {
                "cuda":
                    "kernels-community/layer_norm:LlamaRMSNorm",
                "rocm":
                    "kernels-community/layer_norm:LlamaRMSNorm",
                ...
            },
            ...
        }
        For single device form local
        {
            "RMSNorm":
                "/abs/path:LlamaRMSNorm",
            ...
        },
        For multiple devices form local
        {
            "RMSNorm": {
                "cuda":
                    "/abs/path:LlamaRMSNorm",
                "rocm":
                    "/abs/path:LlamaRMSNorm",
                ...
            },
            ...
        }
        """
        self.store_registered_layer_names(model)
        # Validate that the kernel mapping is a dict
        if not isinstance(self.kernel_mapping, dict):
            raise ValueError(
                f"Kernel mapping must be a dict of the following format: {MAPPING_FORMAT}, got: {type(self.kernel_mapping)}"
            )

        for layer_name, kernel in self.kernel_mapping.items():
            if layer_name not in self.registered_layer_names.values():
                raise ValueError(
                    f"Layer {layer_name} is not registered in the model, please register it first using use_kernel_forward_from_hub"
                )

            if isinstance(kernel, str):
                if "/" not in kernel or ":" not in kernel:
                    raise ValueError(
                        f"Kernel mapping for '{layer_name}' must be a valid repo name with a layer name (e.g., 'org/repo:layer_name' or '/abs/path:layer_name'), got: {kernel}"
                    )

            elif isinstance(kernel, dict):
                for device, repo_name in kernel.items():
                    if device not in ["cuda", "rocm", "xpu", "npu", "neuron"]:
                        raise ValueError(f"Only cuda, rocm, xpu, npu and neuron devices supported, got: {device}")

                    if not isinstance(repo_name, str) or "/" not in repo_name or ":" not in repo_name:
                        raise ValueError(
                            f"Kernel mapping for '{layer_name}' must be a valid repo name with a layer name (e.g., 'org/repo:layer_name' or '/abs/path:layer_name'), got: {repo_name}"
                        )
            else:
                raise ValueError(f"Kernel mapping must follow the format: {MAPPING_FORMAT}, got: {kernel}")