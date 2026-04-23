def check_compatibility(
        self, other: "SystemInfo", device_type: str = "cpu"
    ) -> None:
        """
        Check if this SystemInfo is compatible with another SystemInfo.
        Raises RuntimeError if incompatible.
        """
        if self.python_version != other.python_version:
            raise RuntimeError(
                f"Compile package was created with a different Python version: {self.python_version}"
            )

        if self.torch_version != other.torch_version:
            raise RuntimeError(
                f"Compile package was created with a different PyTorch version: {self.torch_version}"
            )
        if device_type in self.CHECK_GPUS:
            if not getattr(torch, device_type).is_available():
                raise RuntimeError(f"{device_type} is not available")

            if self.toolkit_version != other.toolkit_version:
                raise RuntimeError(
                    f"Compile package was created with a different toolkit version: {self.toolkit_version}"
                )

            if (
                other.triton_version != (0, 0)
                and self.triton_version != other.triton_version
            ):
                raise RuntimeError(
                    f"Compile package was created with a different Triton version: {self.triton_version}"
                )

            # Check GPU name if CUDA/XPU was used
            if other.gpu_name is not None and self.gpu_name != other.gpu_name:
                raise RuntimeError(
                    f"Compile package was created with different GPU: "
                    f"cached={self.gpu_name}, current={other.gpu_name}"
                )