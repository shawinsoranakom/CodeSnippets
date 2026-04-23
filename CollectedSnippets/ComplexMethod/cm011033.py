def wrapper(
            module: _M,
            *args: _P.args,
            **kwargs: _P.kwargs,
        ) -> _M:
            inp_module = module
            modules: list[nn.Module]
            if isinstance(module, nn.Module):
                modules = [module]
            else:
                # If the user passes a sequence of modules, then we assume that
                # we only need to insert the state object on the root modules
                # (i.e. those without a parent) among the passed-in modules.
                # pyrefly: ignore [no-matching-overload]
                modules = _get_root_modules(list(module))
            state = state_cls()  # shared across all modules
            registry_item = RegistryItem()  # shared across all modules

            # `func` is allowed to return different module instances than the
            # input modules as long as FQNs are preserved following the input
            # module order
            all_orig_named_params: list[dict[str, nn.Parameter]] = []
            all_orig_named_buffers: list[dict[str, torch.Tensor]] = []
            all_orig_named_modules: list[dict[str, nn.Module]] = []

            for module in modules:
                default_all_state: dict[Callable, _State] = OrderedDict()
                default_registry: dict[str, RegistryItem] = OrderedDict()
                all_state: dict[Callable, _State] = module.__dict__.setdefault(  # type: ignore[call-overload]
                    STATE_KEY, default_all_state
                )
                if not isinstance(all_state, dict):
                    raise AssertionError(
                        f"Distributed composable API states corrupted: {all_state}"
                    )
                registry: dict[str, RegistryItem] = module.__dict__.setdefault(  # type: ignore[call-overload]
                    REGISTRY_KEY, default_registry
                )
                if not isinstance(registry, dict):
                    raise AssertionError(
                        f"Distributed composable API registry corrupted: {registry}"
                    )
                if func in all_state or func.__name__ in registry:
                    raise AssertionError(
                        "Each distinct composable distributed API can only be applied to a "
                        f"module once. {func.__name__} has already been applied to the "
                        f"following module:\n{module}"
                    )
                all_state.setdefault(func, state)
                registry.setdefault(func.__name__, registry_item)

                all_orig_named_params.append(OrderedDict(module.named_parameters()))
                all_orig_named_buffers.append(OrderedDict(module.named_buffers()))
                all_orig_named_modules.append(OrderedDict(module.named_modules()))

            updated = func(inp_module, *args, **kwargs)
            if updated is None:
                updated = inp_module  # type: ignore[assignment]
            updated_modules: list[nn.Module]
            if isinstance(updated, nn.Module):
                updated_modules = [updated]
            else:
                updated_modules = _get_root_modules(list(inp_module))  # type: ignore[arg-type, call-overload]

            all_new_named_params: list[dict[str, nn.Parameter]] = []
            all_new_named_buffers: list[dict[str, torch.Tensor]] = []
            all_new_named_modules: list[dict[str, nn.Module]] = []
            for module in updated_modules:
                all_new_named_params.append(OrderedDict(module.named_parameters()))
                all_new_named_buffers.append(OrderedDict(module.named_buffers()))
                all_new_named_modules.append(OrderedDict(module.named_modules()))

            num_orig_modules = len(all_orig_named_modules)
            num_new_modules = len(all_new_named_modules)
            if num_orig_modules != num_new_modules:
                raise AssertionError(
                    f"{func.__name__} should return the same number of modules as input modules"
                    f"Inputs: {num_orig_modules} modules\n"
                    f"Outputs: {num_new_modules} modules"
                )

            def check_fqn(orig_fqns: list[str], new_fqns: list[str], check_key: str):
                if orig_fqns == new_fqns:
                    return

                orig_fqn_set, new_fqn_set = set(orig_fqns), set(new_fqns)
                orig_only = orig_fqn_set - new_fqn_set
                new_only = new_fqn_set - orig_fqn_set
                if len(orig_only) or len(new_only):
                    raise RuntimeError(
                        f"{check_key}"
                        "Composable distributed API implementations cannot modify FQNs.\n"
                        f"FQNs only in original: {orig_only}\n"
                        f"FQNs only in new: {new_only}"
                    )
                else:
                    raise RuntimeError(
                        f"{check_key}"
                        "Composable distributed API implementations cannot modify "
                        "the order of FQNs.\n"
                        f"Original FQNs: {orig_only}\n"
                        f"New FQNs: {new_only}"
                    )

            for orig_named_params, new_named_params in zip(
                all_orig_named_params, all_new_named_params
            ):
                check_fqn(
                    list(orig_named_params.keys()),
                    list(new_named_params.keys()),
                    "Checking parameters: ",
                )
            for orig_named_buffers, new_named_buffers in zip(
                all_orig_named_buffers, all_new_named_buffers
            ):
                check_fqn(
                    list(orig_named_buffers.keys()),
                    list(new_named_buffers.keys()),
                    "Checking buffers: ",
                )
            for orig_named_modules, new_named_modules in zip(
                all_orig_named_modules, all_new_named_modules
            ):
                check_fqn(
                    list(orig_named_modules.keys()),
                    list(new_named_modules.keys()),
                    "Checking modules: ",
                )

            # TODO: verify that installed distributed paradigms are compatible with
            # each other.

            return updated