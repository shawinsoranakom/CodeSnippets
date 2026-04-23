def __call__(
        self,
        grid: tuple[int, int, int] = (1, 1, 1),
        block: tuple[int, int, int] = (1, 1, 1),
        args: list | None = None,
        shared_mem: int = 0,
        stream: Any | None = None,
    ) -> None:
        """
        Call the compiled CUDA kernel

        Args:
            grid (tuple): Grid dimensions (grid_x, grid_y, grid_z)
            block (tuple): Block dimensions (block_x, block_y, block_z)
            args (list): List of arguments to pass to the kernel.
                         PyTorch tensor arguments will be automatically converted to pointers.
            shared_mem (int): Shared memory size in bytes
            stream (torch.cuda.Stream): CUDA stream to use. If None, uses current stream.
        """
        import torch

        libcuda = torch.cuda._utils._get_gpu_runtime_library()

        if not args:
            args = []

        # Process arguments and convert tensors to pointers
        processed_args: list[ctypes.c_void_p] = []
        c_args = []

        for arg in args:
            if isinstance(arg, torch.Tensor):
                if not arg.is_cuda and not (arg.is_cpu and arg.is_pinned()):
                    raise ValueError(
                        "All tensor arguments must be CUDA tensors or pinned CPU tensors"
                    )
                # Get pointer to tensor data
                ptr = ctypes.c_void_p(arg.data_ptr())
                processed_args.append(ptr)
                c_args.append(ctypes.byref(ptr))
            elif isinstance(arg, int):
                # Convert integers to C int
                c_int = ctypes.c_int(arg)
                # Store the C int for reference keeping, not in processed_args
                c_args.append(ctypes.byref(c_int))
            elif isinstance(arg, float):
                # Python floats are doubles - use double by default
                c_double = ctypes.c_double(arg)
                # Store the C double for reference keeping, not in processed_args
                c_args.append(ctypes.byref(c_double))
            else:
                raise TypeError(f"Unsupported argument type: {type(arg)}")

        # Convert to array of void pointers
        c_args_array = (ctypes.c_void_p * len(c_args))()
        for i, arg in enumerate(c_args):
            c_args_array[i] = ctypes.cast(arg, ctypes.c_void_p)

        # Get the stream
        if stream is None:
            # Defer import to avoid circular imports
            import torch.cuda

            stream = torch.cuda.current_stream()

        # Check if kernel requires large shared memory but hasn't been configured
        if shared_mem >= 48 * 1024 and (
            self._max_shared_mem_bytes == 0 or shared_mem > self._max_shared_mem_bytes
        ):
            configured_msg = (
                "not configured"
                if self._max_shared_mem_bytes == 0
                else f"only {self._max_shared_mem_bytes} bytes configured"
            )
            raise RuntimeError(
                f"Kernel requires {shared_mem} bytes of shared memory (>= 48KB), "
                f"but {configured_msg}. "
                "Call kernel.set_shared_memory_config(shared_mem) after compilation "
                "and before launching the kernel."
            )

        _check_cuda(
            libcuda.cuLaunchKernel(
                self.func,
                grid[0],
                grid[1],
                grid[2],
                block[0],
                block[1],
                block[2],
                shared_mem,
                stream._as_parameter_,
                c_args_array,
                None,
            )
        )