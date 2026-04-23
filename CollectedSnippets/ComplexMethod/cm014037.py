def wrap_name(module_key: str) -> VariableTracker:
                assert self.param_name_to_source is not None
                self.param_name_to_source[module_key] = source

                # Check if the attr has already been registered. This can happen
                # when two different sources point to the same tensor.
                assert self.root_tx is not None
                if target in self.root_tx.output.side_effects:
                    return self.root_tx.output.side_effects[target]

                if get_static_address_type(target) == "guarded" and not isinstance(
                    source, NumpyTensorSource
                ):
                    install_guard(source.make_guard(GuardBuilder.ID_MATCH))
                elif not is_constant_source(source):
                    install_guard(source.make_guard(GuardBuilder.TENSOR_MATCH))

                vt = wrap_fx_proxy(
                    self.root_tx,
                    tracer.create_proxy("get_attr", module_key, (), {}),
                    example_value=target,
                    **options,
                )

                # Track the object so to avoid duplicate registration in case of
                # different sources pointing to the same tensor object.
                vt = self.root_tx.output.side_effects.track_object_existing(target, vt)

                assert "tensor_dict" not in vt.as_proxy().node.meta
                # pyrefly: ignore [bad-argument-type]
                vt.as_proxy().node.meta["tensor_dict"] = _extract_tensor_dict(target)

                return vt