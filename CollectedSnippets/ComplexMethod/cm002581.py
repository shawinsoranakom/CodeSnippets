def _flash_attn_import_error(
        self,
        flash_attn_version: int,
        general_availability_check: Callable,
        pkg_availability_check: Callable,
        supported_devices: tuple[tuple[Callable, str]],
        custom_supported_devices: tuple[tuple[Callable, str]] = (),
        cuda_min_major_version: int | None = None,
    ):
        """
        Checks whether the specified Flash Attention version is supported and if not, searches for the specific reason
        on why it failed - package import and/or device incompatibility issues.

        Args:
            flash_attn_version (`int`):
                The requested version of Flash Attention.
            general_availability_check (`Callable`):
                Checks whether our `is_available` function detects the specific FA version. Failing reasons
                are then checked for one-by-one.
            pkg_availability_check (`Callable`):
                Checks whether the package could theoretically be detected in the environment by the init structures.
                This is not a sure-fire check as device compatibility with FA is just as important.
            supported_devices (`tuple[tuple[Callable, str]]`):
                Essentially a list (for mutable kwargs reasons a tuple) of the supported devices in the format of
                `(device_availability_check, device_name)`, i.e. a pair of the associated device's name and whether
                it is available in the environment.
            custom_supported_devices (`tuple[tuple[Callable, str]]`, *optional*, defaults to `()`):
                Essentially a list (for mutable kwargs reasons a tuple) of the custom supported devices in the format of
                `(device_availability_check, info_message)`. These custom devices have custom logic outside the torch
                ecosystem either via kernels or other packages and hence have early checks for availability.
            cuda_min_major_version (`int`, *optional*):
                The minimum major cuda version supported for this version of Flash Attention. This is mostly
                affecting more recent versions which are more specialized to the features of new hardware.
        """
        # Certain devices have custom workarounds e.g. with their own package distribution (NPU) or via kernels (XPU)
        for device_availability_check, info_message in custom_supported_devices:
            if device_availability_check():
                logger.info(info_message)
                return

        if not general_availability_check():
            preface = f"FlashAttention{flash_attn_version} has been toggled on, but it cannot be used due to the following error:"

            # Can the package be seen in the import structure
            if not pkg_availability_check():
                raise ImportError(
                    f"{preface} the package for FlashAttention{flash_attn_version} doesn't seem to be installed."
                )
            # Minimum version (FA2 only)
            elif flash_attn_version == 2 and not is_flash_attn_greater_or_equal("2.3.3"):
                raise ImportError(f"{preface} FlashAttention{flash_attn_version} requires at least version `2.3.3`.")
            else:
                # Supported devices availability
                device_availability_checks, device_names = zip(*supported_devices)
                if not any(device_availability_check() for device_availability_check in device_availability_checks):
                    raise ImportError(
                        f"{preface} FlashAttention{flash_attn_version} is not available on CPU. Please make sure you are on any of the supported devices: {device_names}."
                    )
                # Cuda major versions (more recent FA versions are specialized to newer cuda devices)
                elif cuda_min_major_version is not None and is_torch_cuda_available():
                    major, _ = torch.cuda.get_device_capability()
                    if major < cuda_min_major_version:
                        raise ImportError(
                            f"{preface} FlashAttention{flash_attn_version} requires compute capability >= {cuda_min_major_version}, but found {torch.cuda.get_device_capability()} with compute capability {major}.x"
                        )