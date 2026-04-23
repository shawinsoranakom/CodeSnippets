def _raise_tangent_metadata_error(
        expected_type: type | None,
        expected_meta: Any,
        runtime_type: type,
        runtime_meta: Any,
        orig_x: torch.Tensor,
        tangent_idx: int | None,
        tangent_desc: Any | None,
        compile_id_str: str | None,
        tangent_stack_trace: str | None,
    ) -> RuntimeError:
        expected_subclass_got_plain_tensor = (
            expected_type is not None
            and expected_type is not torch.Tensor
            and runtime_type is torch.Tensor
        )
        if expected_subclass_got_plain_tensor:
            tangent_msg = ""
            if tangent_idx is not None:
                tangent_msg = f" (tangent index: {tangent_idx})"

            output_hint = ""
            if tangent_desc is not None:
                from .descriptors import PlainAOTOutput, TangentAOTInput

                if isinstance(tangent_desc, TangentAOTInput) and isinstance(
                    tangent_desc.output, PlainAOTOutput
                ):
                    idx = tangent_desc.output.idx
                    output_hint = f"\n\nThe problematic output is: forward output at index {idx} (0-indexed)"
                else:
                    output_hint = (
                        f"\n\nThe problematic output is: {tangent_desc.expr()}"
                    )

            graph_hint = ""
            if compile_id_str is not None:
                graph_hint = (
                    f"\n\nThis error occurred in compiled graph [{compile_id_str}]."
                )

            stack_trace_hint = ""
            if tangent_stack_trace is not None:
                stack_trace_hint = (
                    f"\n\nThe forward output was created here:\n{tangent_stack_trace}"
                )

            return RuntimeError(
                f"""
During the backward, we encountered a tensor subclass where we guessed its
metadata incorrectly.
Expected a {expected_type.__name__} tangent but got a plain Tensor{tangent_msg}.
This happens when a compiled function returns multiple outputs that
require gradients, but .backward() is only called on some of them.
To fix: call .detach() on forward outputs you don't need gradients for.{output_hint}{graph_hint}{stack_trace_hint}

This error is also more likely to occur if your compiled model is suffering
from a large number of graph breaks. For more advice on finding and fixing
graph breaks, see:
https://docs.pytorch.org/docs/stable/user_guide/torch_compiler/compile/programming_model.graph_breaks_index.html

For more info about this error, see:
https://github.com/pytorch/pytorch/issues/172556"""
            )
        else:
            return RuntimeError(
                f"""
During the backward, we encountered a tensor subclass where we guessed its
metadata incorrectly.
Expected: {expected_meta} (type {expected_type}),
got: {runtime_meta} (type {runtime_type}), shape: {orig_x.shape}.
Your tensor subclass must implement __coerce_same_metadata_as_tangent__."""
            )