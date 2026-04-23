def create_compatible_mapping(self, model, compile=False):
        """
        Transforms a simple kernel_mapping of the form:
            {
                "RMSNorm":
                    "kernels-community/layer_norm:LlamaRMSNorm",
                ...
            },

            or for local path:

            {
                "RMSNorm":
                    "/home/user/liger_kernels:LigerRMSNorm",
                ...
            },

        into a nested mapping:

            {
                "RMSNorm": {
                    "cuda": {
                        Mode.INFERENCE: LayerRepository(
                            repo_id="kernels-community/layer_norm",
                            layer_name="LlamaRMSNorm",
                        )
                    }
                }
            }

            or for local path:

            {
                "RMSNorm": {
                    "cuda": {
                        Mode.INFERENCE: LocalLayerRepository(
                            repo_path=Path("/home/user/liger_kernels"),
                            package_name="liger_kernels",
                            layer_name="LigerRMSNorm",
                        )
                    }
                }
            }

        that's compatible with the kernels library.

        The device is inferred from the model's parameters if not provided.
        The Mode is inferred from the model's training state.
        """
        from kernels import Mode

        compatible_mapping = {}
        current_device = infer_device(model)
        for layer_name, kernel in self.kernel_mapping.items():
            # Infer Mode: use Mode.TRAINING if model is training, else use Mode.INFERENCE
            mode = Mode.TRAINING if model.training else Mode.INFERENCE
            if compile:
                mode = mode | Mode.TORCH_COMPILE

            if isinstance(kernel, str):
                repo_name = kernel
                if not self.use_local_kernel:
                    add_to_mapping(layer_name, current_device, repo_name, mode, compatible_mapping)
                else:
                    add_to_mapping_local(layer_name, current_device, repo_name, mode, compatible_mapping)
            elif isinstance(kernel, dict):
                for device, repo_name in kernel.items():
                    if device != current_device:
                        continue
                    if not self.use_local_kernel:
                        add_to_mapping(layer_name, device, repo_name, mode, compatible_mapping)
                    else:
                        add_to_mapping_local(layer_name, device, repo_name, mode, compatible_mapping)

        self.kernel_mapping = compatible_mapping