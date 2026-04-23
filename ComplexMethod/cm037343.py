def block_size_is_supported(
        backends: list[type[AttentionBackend]], block_size: int
    ) -> bool:
        """Check if the block size is supported by all backends."""
        for backend in backends:
            is_supported = False
            for supported_size in backend.get_supported_kernel_block_sizes():
                if isinstance(supported_size, int):
                    if block_size == supported_size:
                        is_supported = True
                elif isinstance(supported_size, MultipleOf):
                    if block_size % supported_size.base == 0:
                        is_supported = True
                else:
                    raise ValueError(f"Unknown supported size: {supported_size}")
            if not is_supported:
                return False
        return True