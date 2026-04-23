def install(self, backends: dict[_BackendId, Any]) -> None:
        """
        Sync the package states to the compiled function. This includes the following actions:
          1. Clean up the previously installed states.
          2. Install the compiled functions to global scopes.
          3. Install the precompiled cache entries to ExtraStates on the code object.
        """
        from torch._C._dynamo.eval_frame import _load_precompile_entry

        from .output_graph import get_builtins_dict

        self.uninstall()
        for code, entry in self._codes.items():
            context = (
                _compile_frame_context(code)
                if entry.has_compile_id
                else contextlib.nullcontext()
            )
            with context:
                module = sys.modules[entry.python_module]
                for alias, module_name in entry.import_sources.items():
                    self._install_global(
                        module, alias, importlib.import_module(module_name)
                    )
                target_code = code
                if entry.install_to_global:
                    for function_name in entry.function_names:
                        if code.co_freevars:
                            # Resume functions with freevars need a factory
                            # that takes a closure tuple, matching
                            # install_resume_function_global in output_graph.py.
                            f_globals = module.__dict__
                            fn_name = function_name

                            def _make_fn(
                                closure: tuple[types.CellType, ...],
                                _code: types.CodeType = code,
                                _globals: dict[str, Any] = f_globals,
                                _name: str = fn_name,
                            ) -> types.FunctionType:
                                return types.FunctionType(
                                    _code, _globals, _name, None, closure
                                )

                            self._install_global(module, function_name, _make_fn)
                        else:
                            fn = types.FunctionType(
                                code, module.__dict__, function_name
                            )
                            self._install_global(module, function_name, fn)
                if entry.code_source:
                    target_code = _lookup_code(entry)

                if entry.bypassed:
                    # If the entry is bypassed, do not install backends
                    # or guarded codes.
                    continue

                for backend_id in entry.backend_ids:
                    if backend_id not in backends:
                        raise RuntimeError(
                            f"Backend {backend_id} is not found in the given backends"
                        )
                    with dynamo_timed(
                        "after_deserialization", phase_name="backend_compile"
                    ):
                        backend = backends[backend_id].after_deserialization()
                        self._install_global(
                            module,
                            backend_id,
                            torch._dynamo.disable(backend),
                        )

                if len(entry.guarded_codes) == 0:
                    # Dynamo generates empty graph for trivial functions, should just skip them
                    # in these cases.
                    torch._dynamo.eval_frame.skip_code(target_code)

                for guarded_code in entry.guarded_codes:
                    with dynamo_timed("precompile_load_guards"):
                        guards_state = load_guards_state(guarded_code.guards_state)
                    runtime_global_scope = sys.modules[entry.python_module].__dict__
                    # The installed builtins dict might be absent from the runtime
                    # while loading guards. Populate it if it's missing.
                    if (
                        builtin_dict_name
                        := guards_state.output_graph.name_of_builtins_dict_key_in_fglobals
                    ):
                        builtins_dict = get_builtins_dict(runtime_global_scope)
                        if builtin_dict_name in runtime_global_scope:
                            assert (
                                runtime_global_scope[builtin_dict_name] is builtins_dict
                            )
                        else:
                            runtime_global_scope[builtin_dict_name] = builtins_dict
                    assert isinstance(guards_state, torch._dynamo.guards.GuardsState)
                    with dynamo_timed("precompile_build_guards"):
                        guard_manager = load_guard_manager(
                            guards_state, target_code, runtime_global_scope
                        )
                    _load_precompile_entry(
                        target_code,
                        guard_manager,
                        SerializedCode.to_code_object(guarded_code.dynamo_code),
                    )