def create_proxy(
        self,
        kind: str,
        target: torch.fx.node.Target,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
        name: str | None = None,
        type_expr: Any = None,
        proxy_factory_fn: Callable[[Node], Proxy] | None = None,
    ) -> MetaProxy:
        rv = super().create_proxy(
            kind,
            target,
            args,
            kwargs,
            name,
            type_expr,
            # pyrefly: ignore [bad-argument-type]
            proxy_factory_fn,
        )

        if kind == "placeholder" and target in self.meta_args:
            rv.install_tensor_meta(self.meta_args[target])
            return rv  # pyrefly: ignore [bad-return]

        if target in self.orig_fns:
            # NOTE: tensor constructors in PyTorch define the `device` argument as
            # *kwargs-only*. That is why this works. If you add methods to
            # _TORCH_METHODS_TO_PATCH that do not define `device` as kwarg-only,
            # this will break and you will likely see issues where we cannot infer
            # the size of the output.
            if "device" in kwargs:
                kwargs["device"] = "meta"

        try:
            args_metas = torch.fx.node.map_aggregate(args, proxys_to_metas)
            kwargs_metas = torch.fx.node.map_aggregate(kwargs, proxys_to_metas)

            if kind == "call_function":
                # pyrefly: ignore [no-matching-overload]
                meta_target = manual_meta_overrides.get(target, target)

                meta_out = meta_target(*args_metas, **kwargs_metas)
            elif kind == "call_method":
                meta_target = getattr(args_metas[0], target)  # type: ignore[index]
                meta_out = meta_target(*args_metas[1:], **kwargs_metas)  # type: ignore[index]
            elif kind == "call_module":
                if not hasattr(self, "orig_forward"):
                    raise AssertionError("orig_forward not set for call_module")
                self._disable_module_getattr = True
                try:
                    # pyrefly: ignore [bad-argument-type]
                    mod = self.root.get_submodule(target)
                    mod_type = type(mod)
                    if mod_type in manual_meta_overrides:
                        meta_out = manual_meta_overrides[mod_type](
                            mod, *args_metas, **kwargs_metas
                        )  # type: ignore[misc, arg-type]
                    else:
                        meta_out = self.orig_forward(*args_metas, **kwargs_metas)
                finally:
                    self._disable_module_getattr = False
            elif kind == "get_attr":
                self._disable_module_getattr = True
                try:
                    attr_itr = self.root
                    atoms = target.split(".")  # pyrefly: ignore [missing-attribute]
                    for atom in atoms:
                        attr_itr = getattr(attr_itr, atom)
                    if not isinstance(attr_itr, torch.Tensor):
                        raise AssertionError(f"Expected Tensor, got {type(attr_itr)}")
                    meta_out = attr_itr.to(device="meta")
                finally:
                    self._disable_module_getattr = False
            else:
                return rv  # pyrefly: ignore [bad-return]

            # TODO
            if not isinstance(rv, torch.fx.Proxy):
                raise AssertionError("Dont support composite output yet")
            rv.install_tensor_meta(meta_out)
        except Exception as e:
            warnings.warn(f"Could not compute metadata for {kind} target {target}: {e}")

        return rv