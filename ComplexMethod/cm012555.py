def halide_kernel_meta(self) -> HalideMeta:
        """Compute metadata required by codecache.py"""
        argtypes = []
        for _, arg in self.halide_argdefs():
            if isinstance(arg, SizeArg):
                shape = None
                stride = None
                offset = None
                dtype = "long"
            else:
                shape = [
                    cexpr(self.rename_indexing(x.size))
                    for x in self.buffer_dimensions[arg.name]
                ]
                stride = [
                    cexpr(self.rename_indexing(x.stride))
                    for x in self.buffer_dimensions[arg.name]
                ]
                assert len(shape) == len(stride)
                offset = cexpr(self.buffer_offsets[arg.name])
                dtype = f"{DTYPE_TO_CPP[arg.dtype]}*"
            argtypes.append(
                HalideInputSpec(
                    dtype,
                    arg.name,
                    shape=shape,
                    stride=stride,
                    offset=offset,
                    alias_of=arg.alias_of,
                )
            )

        current_device = V.graph.get_current_device_or_throw()
        if current_device.type == "cpu":
            target = [config.halide.cpu_target]
            scheduler = config.halide.scheduler_cpu
            scheduler_flags = {
                "parallelism": parallel_num_threads(),
            }
            cuda_device = None
        else:
            assert current_device.type == "cuda", "only cpu/cuda supported"
            assert current_device.index <= 0, "only default device supported"
            target = [config.halide.gpu_target]
            scheduler = config.halide.scheduler_cuda
            capability = torch.cuda.get_device_properties(current_device)
            if "cuda_capability" not in target[0]:
                for major, minor in [(8, 6), (8, 0), (7, 5), (7, 0), (6, 1)]:
                    if capability.major >= major and capability.minor >= minor:
                        target.append(f"cuda_capability_{major}{minor}")
                        break
            target.append("user_context")
            scheduler_flags = {
                "parallelism": capability.multi_processor_count,
                # TODO(jansel): explore other flags, see:
                # grep parser.parse ~/Halide/src/autoschedulers/anderson2021/AutoSchedule.cpp
            }
            cuda_device = max(0, current_device.index)

        # strict_float is requires for correctness
        target.append("strict_float")

        # without this we will initialize cuda once per kernel and hit errors
        target.append("no_runtime")

        if not config.halide.asserts:
            target.append("no_asserts")

        if config.halide.debug:
            target.append("debug")

        if "64" in self.index_dtype:
            # TODO(jansel): it is unclear if this does anything, since input sizes are still int32
            target.append("large_buffers")

        return HalideMeta(
            argtypes,
            target="-".join(target),
            scheduler=scheduler,
            scheduler_flags=scheduler_flags,  # type: ignore[arg-type]
            cuda_device=cuda_device,
        )