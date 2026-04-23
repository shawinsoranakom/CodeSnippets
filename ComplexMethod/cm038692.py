def post_init_cudagraph_sizes(self) -> None:
        """To complete the initialization after cudagraph related
        configs are set. This includes:
        - initialize compile_sizes
        """

        computed_compile_sizes: list[int] = []
        if self.compile_sizes is not None:
            # de-duplicate the sizes provided by the config
            self.compile_sizes = list(set(self.compile_sizes))
            for x in self.compile_sizes:
                if isinstance(x, str):
                    assert x == "cudagraph_capture_sizes", (
                        "Unrecognized size type in compile_sizes, "
                        f"expect 'cudagraph_capture_sizes', got {x}"
                    )
                    computed_compile_sizes.extend(self.cudagraph_capture_sizes)
                else:
                    assert isinstance(x, int)
                    computed_compile_sizes.append(x)
        self.compile_sizes = computed_compile_sizes  # type: ignore

        # make sure the sizes are in ascending order
        self.cudagraph_capture_sizes.sort()
        if self.cudagraph_capture_sizes:
            assert self.cudagraph_capture_sizes[-1] == self.max_cudagraph_capture_size