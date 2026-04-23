def _codegen_buffer(cls, name: str, arg: HalideInputSpec, cuda: bool) -> list[str]:
        assert arg.shape is not None
        assert arg.stride is not None and len(arg.shape) == len(arg.stride)
        assert arg.offset is not None
        data_ptr = f"{arg.alias_of or arg.name} + {arg.offset}"
        if cuda:
            device = f"reinterpret_cast<uint64_t>({data_ptr})"
            device_interface = "cuda_interface"
            host = "nullptr"
            flags = "halide_buffer_flag_device_dirty"
        else:
            device = "0"
            device_interface = "nullptr"
            host = f"reinterpret_cast<uint8_t*>({data_ptr})"
            flags = "halide_buffer_flag_host_dirty"

        dims = []
        for size, stride in zip(arg.shape, arg.stride):
            dims.append(f"halide_dimension_t(0, {size}, {stride})")

        return [
            f"halide_buffer_t {name};",
            f"halide_dimension_t {name}_dims[] = {{{', '.join(dims)}}};"
            if len(dims) > 0
            else f"halide_dimension_t * {name}_dims = nullptr;",
            f"{name}.device = {device};",
            f"{name}.device_interface = {device_interface};",
            f"{name}.host = {host};",
            f"{name}.flags = {flags};",
            f"{name}.type = {arg.halide_type()};",
            f"{name}.dimensions = {len(dims)};",
            f"{name}.dim = {name}_dims;",
            f"{name}.padding = nullptr;",
        ]