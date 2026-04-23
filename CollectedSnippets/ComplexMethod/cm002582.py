def _flash_attn_can_dispatch(self, flash_attn_version: int, is_init_check: bool = False) -> bool:
        """
        Check the availability of Flash Attention for a given model.

        Args:
            flash_attn_version (`int`):
                The requested version of Flash Attention.
            is_init_check (`bool`, *optional*):
                Whether this check is performed early, i.e. at __init__ time, or later when the model and its weights are
                fully instantiated. This is needed as we also check the devices of the weights, which are only available
                later after __init__. This allows to raise proper exceptions early before instantiating the full models
                if we know that the model does not support the requested attention.
        """
        if not self._supports_flash_attn:
            raise ValueError(
                f"{self.__class__.__name__} does not support Flash Attention {flash_attn_version} yet. Please request to add support where"
                f" the model is hosted, on its model hub page: https://huggingface.co/{self.config._name_or_path}/discussions/new"
                " or in the Transformers GitHub repo: https://github.com/huggingface/transformers/issues/new"
            )

        if flash_attn_version not in [2, 3, 4]:
            raise ValueError(f"Requested Flash Attention {flash_attn_version} which is not supported.")

        # Check if we can even use the FA version based on the env of the user
        self._flash_attn_import_error(**FLASH_ATTENTION_COMPATIBILITY_MATRIX[flash_attn_version])

        # Check for attention dropout, which is incompatible with newer FA versions
        # (many should not really care about dropout as it is not super effective, hence warning for now)
        if flash_attn_version > 2:
            if hasattr(self.config, "attention_dropout") and self.config.attention_dropout > 0:
                logger.warning_once(
                    f"You are attempting to use Flash Attention {flash_attn_version} with dropout. "
                    "This might lead to unexpected behaviour as this is not supported on recent versions of Flash Attention."
                )

        # People often move dtypes after init so we only warn in those cases
        dtype = self.config.dtype
        if dtype is None:
            logger.warning_once(
                f"You are attempting to use Flash Attention {flash_attn_version} without specifying a dtype. This might lead to unexpected behaviour"
            )
        elif dtype is not None and dtype not in [torch.float16, torch.bfloat16]:
            logger.warning_once(
                f"Flash Attention {flash_attn_version} only supports torch.float16 and torch.bfloat16 dtypes, but"
                f" the current dype in {self.__class__.__name__} is {dtype}. You should run training or inference using Automatic Mixed-Precision via the `with torch.autocast(device_type='torch_device'):` decorator,"
                f' or load the model with the `dtype` argument. Example: `model = AutoModel.from_pretrained("meta-llama/Llama-3.2-1B", attn_implementation="flash_attention_{flash_attn_version}", dtype=torch.float16)`'
            )

        # With the early check, the parameters are not yet initialized correctly
        if not is_init_check:
            param_devices = list({param.device for param in self.parameters()})
            if len(param_devices) == 1 and param_devices[0].type == "cpu":
                found_device = False
                for device_availability_check, device_name in FLASH_ATTENTION_COMPATIBILITY_MATRIX[flash_attn_version][
                    "supported_devices"
                ]:
                    if device_availability_check():
                        found_device = True
                        logger.warning_once(
                            f"You are attempting to use Flash Attention {flash_attn_version} with a model not initialized on GPU. Please make sure to have "
                            "access to a GPU and either initialise the model on a GPU by passing a device_map or initialising the model on CPU and then "
                            f"moving it to GPU, e.g. with `model.to('{device_name}')`."
                        )
                        break

                if not found_device:
                    raise ValueError(
                        f"You are attempting to use Flash Attention {flash_attn_version} with a model not initialized on GPU and with no GPU available. "
                        "This is not supported yet. Please make sure to have access to a GPU and either initialise the model on a GPU by passing a device_map "
                        "or initialising the model on CPU and then moving it to GPU."
                    )

        # If no error raise by this point, we can return `True`
        return True