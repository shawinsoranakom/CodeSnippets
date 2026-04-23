def __torch_function__(
        self,
        func: OpOverload | Callable[..., Any],
        types: tuple[torch._C._TensorMeta, ...],
        args: tuple[object, ...] = (),
        kwargs: dict[str, object] | None = None,
    ) -> object:
        kwargs = kwargs or {}
        if func in _side_effectful_need_to_be_preserved_pre_dispatch:
            # It's for passing the export verifier which needs to verify the meta['val']
            # TODO(tmanlaibaatar): we should systematically couple it with export verifier,
            # instead of hardcoding it here.
            # T203648563
            if func is torch.amp.autocast_mode._exit_autocast:
                enter_node = self.enter_autocast_nodes.pop()
                args = (enter_node,)
            node = self.tracer.create_node("call_function", func, args, {})  # type: ignore[arg-type]
            if func is torch.amp.autocast_mode._enter_autocast:
                self.enter_autocast_nodes.append(node)
            if func in [
                torch._C._set_grad_enabled,
                torch.amp.autocast_mode._enter_autocast,
                torch.amp.autocast_mode._exit_autocast,
            ]:
                node.meta["val"] = None
            # For autocast, the python APIs run so we don't have to run them again
            # here.
            if func is torch._C._set_grad_enabled:
                # pyrefly: ignore [bad-argument-type]
                func(*args, **kwargs)
            return node

        # We need more complicated handling here because the inputs
        # to these functions are sometimes tensors or symints where
        # we need to fetch the proxies properly.
        if func in [
            torch._functorch.predispatch._add_batch_dim,
            torch._functorch.predispatch._remove_batch_dim,
            torch._functorch.predispatch._vmap_increment_nesting,
            torch._functorch.predispatch._vmap_decrement_nesting,
            torch._functorch.vmap.lazy_load_decompositions,
            torch._functorch.predispatch._make_dual,
            torch._functorch.predispatch._unpack_dual,
            torch._functorch.predispatch._jvp_increment_nesting,
            torch._functorch.predispatch._jvp_decrement_nesting,
            torch._functorch.predispatch._unwrap_for_grad,
            torch._functorch.predispatch._enter_dual_level,
            torch._functorch.predispatch._exit_dual_level,
        ]:
            _, proxies, _ = _fetch_proxies_and_all_constant_flag(args, self.tracer)
            out_proxy = self.tracer.create_proxy(
                "call_function",
                func,
                proxies,
                kwargs,
            )
            res = func(*args, **kwargs)
            # When JVP transforms are active, snapshot_fake calls detach
            # which goes through C++ functorch dispatch keys, potentially
            # re-wrapping the result as a grad tracking tensor.
            # Temporarily disable functorch transforms during tracking to
            # prevent this corruption of meta["val"].
            if func in _jvp_predispatch_functions:
                with torch._C._DisableFuncTorch():
                    track_tensor_tree(res, out_proxy, constant=None, tracer=self.tracer)
            else:
                track_tensor_tree(res, out_proxy, constant=None, tracer=self.tracer)
            return res
        return func(*args, **kwargs)