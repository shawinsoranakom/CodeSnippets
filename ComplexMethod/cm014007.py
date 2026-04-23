def convert(gm: torch.fx.GraphModule) -> str:
        from torch.nn.modules.module import _addindent

        tab = " " * 4

        model_str = textwrap.dedent(
            """
            from torch.nn import *
            class Repro(torch.nn.Module):
                def __init__(self) -> None:
                    super().__init__()
            """
        )

        for module_name, module in gm.named_children():
            module_str = f"{module.__repr__()}"
            # module should be a core torch.nn.Module, so all parameters
            # should be on the same device.
            example_param = next(module.parameters(), None)
            if example_param is not None and example_param.is_cuda:
                module_str = f"{module_str}.cuda()"
            model_str += f"{tab * 2}self.{module_name} = {module_str}\n"

        for buffer_name, buffer in gm._buffers.items():
            if buffer is None:
                continue
            # Serialize full data for small buffers
            if buffer.numel() <= MAX_CONSTANT_NUMEL_INLINE:
                from torch._tensor_str import PRINT_OPTS

                assert PRINT_OPTS.threshold >= MAX_CONSTANT_NUMEL_INLINE
                tensor_str = repr(buffer)
            elif torch.is_floating_point(buffer):
                tensor_str = f"torch.randn({list(buffer.shape)}, dtype={buffer.dtype})"
            else:
                tensor_str = (
                    f"torch.randint(1, size={list(buffer.shape)}, dtype={buffer.dtype})"
                )
            if buffer.is_cuda:
                tensor_str = f"{tensor_str}.cuda()"
            model_str += (
                f"{tab * 2}self.register_buffer('{buffer_name}', {tensor_str})\n"
            )

        for param_name, param in gm._parameters.items():
            if param is None:
                continue
            maybe_device = ""
            if param.is_cuda:
                maybe_device = ', device="cuda"'
            tensor_str = f"torch.nn.Parameter(torch.randn({list(param.shape)}, dtype={param.dtype}{maybe_device}))"
            model_str += f"{tab * 2}self.{param_name} = {tensor_str}\n"

        # TODO - Keep this code for now. But, I don't think we will need this.
        # attrs = dir(gm)
        # for attr in attrs:
        #     if "_tensor_constant" in attr:
        #         val = getattr(gm, attr)
        #         model_str += f"    {attr} = {val!r}\n"

        model_str += f"{_addindent(gm.code, 4)}\n"
        return model_str