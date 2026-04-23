def get_attr(
        self,
        target: str,  # type: ignore[override]
        args: tuple[()],  # type: ignore[override]
        kwargs: dict[str, object],
    ) -> Constant | TensorBox | ShapeAsConstantBuffer | ir.Subgraph | TorchBindObject:
        # this is a constant
        value = getattr_recursive(self.module, target)  # type: ignore[arg-type]

        if isinstance(value, torch.fx.GraphModule):
            # Reuse the existing subgraph if we have seen it before already.
            if target in self.seen_subgraphs:
                return self.seen_subgraphs[target]

            out = ir.Subgraph(name=target, graph_module=value)
            self.seen_subgraphs[target] = out
            return out

        if isinstance(value, torch._C.ScriptObject):
            self.torchbind_constants[target] = value
            self.constant_reprs[target] = ""
            return TorchBindObject(name=target, value=value)
        elif isinstance(value, FakeScriptObject):
            self.torchbind_constants[target] = value
            self.constant_reprs[target] = ""
            return TorchBindObject(name=target, value=value)
        elif is_opaque_type(type(value)):
            self.torchbind_constants[target] = value  # type: ignore[arg-type]
            self.constant_reprs[target] = ""
            return TorchBindObject(name=target, value=value)  # type: ignore[arg-type]

        assert isinstance(value, torch.Tensor)
        if (
            config.aot_inductor.use_runtime_constant_folding
            or config.always_keep_tensor_constants
            or unsupported_output_tensor(value)
            or target in self.mutated_named_buffers
        ):
            return self.add_tensor_constant(value, target)

        with no_dispatch():
            if value.shape == ():
                return Constant(
                    value=value.item(), dtype=value.dtype, device=value.device
                )
            if self.can_inline_constant(value):
                log.debug("Inlining constant: %s ", target)
                # tensor lowering has constant inlining logic
                from .lowering import tensor

                return tensor(value.tolist(), dtype=value.dtype, device=value.device)

        return self.add_tensor_constant(value, target)