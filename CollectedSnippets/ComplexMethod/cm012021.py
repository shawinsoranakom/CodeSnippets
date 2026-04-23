def generate_output(output: Any, indices: list[tuple[Any, int]]) -> Any:
            if isinstance(output, (list, tuple)):
                return type(output)(
                    generate_output(output[i], indices + [(type(output), i)])
                    for i in range(len(output))
                )
            elif isinstance(output, dict):
                return {
                    key: generate_output(val, indices + [(type(output), key)])
                    for key, val in output.items()
                }
            elif isinstance(output, torch.Tensor):
                buf = MultiOutput(
                    cls.tensor_to_layout(output),
                    packed,
                    indices,
                )
                if (
                    config.assume_unaligned_fallback_output
                    or has_unaligned_input
                    or not tensor_is_aligned(output)
                ):
                    V.graph.unaligned_buffers.add(buf.name)  # type: ignore[arg-type]
                return buf
            elif isinstance(output, int):
                return output
            elif isinstance(output, torch.SymInt):
                return output.node.expr
            elif isinstance(
                output, (torch._C.ScriptObject, FakeScriptObject)
            ) or is_opaque_value(output):
                return OpaqueMultiOutput(
                    NoneLayout(device=device),
                    packed,
                    indices,
                    output,
                )
            else:
                assert output is None, (
                    f"FallbackKernel output type {type(output)} is not supported"
                )
                return None