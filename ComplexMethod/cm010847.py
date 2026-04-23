def functional_call(*args: Any, **kwargs: Any) -> Any:
        flat_params = args[:params_len]
        if isinstance(params_spec, TreeSpec):
            params = pytree.tree_unflatten(flat_params, params_spec)
        else:
            if not isinstance(params_spec, list):
                raise AssertionError(
                    f"expected params_spec to be a list, got {type(params_spec)}"
                )
            params = dict(zip(params_spec, flat_params))
        with (
            stateless._reparametrize_module(mod, params),
            maybe_disable_thunkify(),
        ):
            if isinstance(mod, torch.fx.GraphModule):
                if kwargs:
                    # Handle **kwargs. FX only natively supports positional
                    # arguments (through placeholders).
                    arg_list = list(args[params_len:])
                    arg_list.extend(list(kwargs.values()))
                    args = tuple(arg_list)
                else:
                    args = args[params_len:]

                with fx_traceback.preserve_node_meta(), warnings.catch_warnings():
                    warnings.filterwarnings(
                        "ignore", "Anomaly Detection has been enabled."
                    )
                    with torch.autograd.detect_anomaly(check_nan=False):
                        fake_mode = detect_fake_mode()
                        if fake_mode is None:
                            raise AssertionError("fake_mode must not be None")
                        fake_mode.epoch += 1
                        out = PropagateUnbackedSymInts(mod).run(*args)
            else:
                out = mod(*args[params_len:], **kwargs)

        if strict_out_tuple and not isinstance(out, (tuple, list)):
            raise RuntimeError(
                "Graph output must be a (). This is so that we can avoid "
                "pytree processing of the outputs. Please change the module to "
                "have tuple outputs or use aot_module instead."
            )
        return out