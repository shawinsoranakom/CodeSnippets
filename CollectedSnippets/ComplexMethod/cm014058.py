def proxy_call_backward(
        self,
        inputs: Sequence[Any],
        output_metadatas: Sequence[Any],
        saved_tensors: Sequence[torch.Tensor],
        backward_idx: int,
        ctx: torch.autograd.function.BackwardCFunction,
        maybe_backward_state_idx: int | None,
        opaque_object_indices: list[int],
    ) -> tuple[torch.Tensor | None, ...]:
        assert self.hooks_proxy is not None
        pctx = self.hooks_proxy[backward_idx]  # type: ignore[index]
        pinputs = self.to_proxy(inputs)
        psaved_tensors = self.to_proxy(saved_tensors)
        if hasattr(ctx._forward_cls, "_aot_id"):  # type: ignore[attr-defined]
            # AOT backward
            proxies = self.proxy_call_aot_backward(
                pinputs,
                psaved_tensors,
                saved_tensors,
                pctx,
                ctx,
                maybe_backward_state_idx,
                opaque_object_indices,
            )
        else:
            if getattr(ctx._forward_cls, "boxed_grads_call", False):  # type: ignore[attr-defined]
                raise RuntimeError(
                    f"boxed_grads_call=True on {ctx._forward_cls.__name__} "  # type: ignore[attr-defined]
                    "is not supported with compiled autograd. "
                )
            proxies = self.fx_tracer.create_proxy(
                kind="call_function",
                target=call_backward,
                args=(
                    pctx,
                    psaved_tensors,
                    *pinputs,
                ),
                kwargs={},
            )
        assert proxies is not None

        with disable_proxy_modes_tracing():
            # create fake Tensors
            grad_ins: list[torch.Tensor | None] = []
            for idx, output_metadata in enumerate(output_metadatas):
                if output_metadata is None or proxies[idx] is None:
                    grad_ins.append(None)
                    continue

                layout, device, dtype, size = output_metadata
                grad_ins.append(
                    torch.empty(size=size, dtype=dtype, layout=layout, device=device)
                )
            self.bind_objects_to_proxies(grad_ins, proxies)
        return tuple(grad_ins)