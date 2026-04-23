def compile_check_fn(
        self,
        builder: GuardBuilder,
        guards_out: list[Guard],
        guard_fail_fn: Callable[[GuardFail], None] | None,
    ) -> None:
        # see parallel handling of ".0" / "___implicit0" in _eval_frame.c
        largs = builder.argnames
        largs += ["**___kwargs_ignored"]

        guards_log.debug("GUARDS:")

        # pyrefly: ignore [implicit-any]
        code_parts = []
        verbose_code_parts = []
        structured_guard_fns: list[Callable[[], dict[str, Any]]] = []

        # Add compile id info in the guard manager for debugging purpose
        self.guard_manager.root.attach_compile_id(
            str(CompileContext.current_compile_id())
        )

        # Clear references to torch_function modes held in the list
        self.torch_function_mode_stack = None

        def add_code_part(
            code_part: str, guard: Guard | None, log_only: bool = False
        ) -> None:
            verbose_code_part = get_verbose_code_part(code_part, guard)
            guards_log.debug("%s", verbose_code_part)

            structured_guard_fns.append(
                lambda: {
                    "code": code_part,
                    "stack": (
                        structured.from_traceback(guard.stack.summary())
                        if guard and guard.stack
                        else None
                    ),
                    "user_stack": (
                        structured.from_traceback(guard.user_stack)
                        if guard and guard.user_stack
                        else None
                    ),
                }
            )

            if verbose_guards_log.isEnabledFor(logging.DEBUG):
                maybe_stack = ""
                maybe_user_stack = ""
                if guard is not None:
                    if guard.stack:
                        maybe_stack = f"\nStack:\n{''.join(guard.stack.format())}"
                    if guard.user_stack:
                        maybe_user_stack = (
                            f"\nUser stack:\n{''.join(guard.user_stack.format())}"
                        )
                verbose_guards_log.debug(
                    "Guard: %s%s%s",
                    code_part,
                    maybe_stack,
                    maybe_user_stack,
                )

            if not log_only:
                code_parts.append(code_part)
                verbose_code_parts.append(verbose_code_part)

        seen = set()
        for gcl in builder.code:
            for code in gcl.code_list:
                if code not in seen:
                    # If Cpp guard manager is enabled, we don't need to add to
                    # code_parts.
                    add_code_part(code, gcl.guard, True)
                    seen.add(code)

        no_tensor_aliasing_names = builder.no_tensor_aliasing_names
        check_tensors_fn = None
        check_tensors_verbose_fn = None

        if len(no_tensor_aliasing_names) > 1:
            # Install tensor aliasing guard. TENSOR_MATCH guards are already
            # installed for cpp guard manager.
            install_no_tensor_aliasing_guard(
                builder.no_tensor_aliasing_guard_managers,
                no_tensor_aliasing_names,
                ["check_no_aliasing(" + ", ".join(no_tensor_aliasing_names) + ")"],
                None,
            )

        # Note - On Lambda guarding of object aliasing
        # We previously installed object-aliasing guards as relational guards,
        # but that undermined the recursive-dict guard optimization: placing the
        # aliasing guard at a leaf prevented the parent dict node from
        # qualifying as a recursive-dict guard root. Because aliasing guards are
        # rare, we now emit them as epilogue guards via a small Python lambda.
        # This repeats the access in Python—adding a bit of work—but the
        # overhead is outweighed by the gains from enabling recursive-dict guard
        # optimization.
        if (
            config.use_lamba_guard_for_object_aliasing
            and builder.object_aliasing_guard_codes
        ):
            aliasing_code_parts, aliasing_verbose_code_parts = map(
                list, zip(*builder.object_aliasing_guard_codes)
            )
            builder.add_python_lambda_leaf_guard_to_root(
                aliasing_code_parts, aliasing_verbose_code_parts
            )

        aotautograd_guards: list[GuardEnvExpr] = (
            self.output_graph.aotautograd_guards if self.output_graph else []
        )

        # TODO(anijain2305) - There is a duplicate logic in Dynamo to find
        # aliased input tensors. So most probably we don't need this here.
        # Revisit.
        for guard in aotautograd_guards:
            if isinstance(guard, DuplicateInputs):
                source_a = guard.input_source_a
                source_b = guard.input_source_b
                code_part = f"{source_a.name} is {source_b.name}"
                install_object_aliasing_guard(
                    builder.get_guard_manager_from_source(source_a),
                    builder.get_guard_manager_from_source(source_b),
                    [code_part],
                    None,
                )
                add_code_part(code_part, None, True)
            elif isinstance(guard, StorageOverlap):
                overlapping_guard_managers = [
                    builder.get_guard_manager_from_source(s)
                    for s in guard.overlapping_sources
                ]
                non_overlapping_guard_managers = [
                    builder.get_guard_manager_from_source(s)
                    for s in guard.non_overlapping_sources
                ]
                code_part = (
                    """check_overlapping("""
                    f"""overlapping=[{", ".join(s.name for s in guard.overlapping_sources)}], """
                    f"""non_overlapping=[{", ".join(s.name for s in guard.non_overlapping_sources)}])"""
                )
                install_storage_overlapping_guard(
                    overlapping_guard_managers,
                    non_overlapping_guard_managers,
                    [code_part],
                    None,
                )
                add_code_part(code_part, None, True)
            else:
                raise RuntimeError(f"Unknown GuardEnvExpr: {guard}")

        # TODO: the "guard" here is actually just the top level SHAPE_ENV
        # which is useless.  Get ShapeEnv to pass in more provenance.
        for gcl in builder.shape_env_code:
            for code in gcl.code_list:
                # Shape env guards are already added for CPP guard manager in
                # SHAPE_ENV implementation.
                add_code_part(code, gcl.guard, True)

        # OK, all done generating guards
        if structured_guard_fns:
            torch._logging.trace_structured(
                "dynamo_guards", payload_fn=lambda: [f() for f in structured_guard_fns]
            )

        if convert_frame.initial_global_state is None:
            # we should only hit this case in NopTests()
            check_global_state = convert_frame.GlobalStateGuard().check
        else:
            check_global_state = getattr(self.global_state, "check", None)
        closure_vars = {
            "___check_tensors": check_tensors_fn,
            "___check_tensors_verbose": check_tensors_verbose_fn,
            "___check_global_state": check_global_state,
            "___check_torch_function_mode_stack": self.torch_function_mode_stack_check_fn,
            **SYMPY_INTERP,
            **_get_closure_vars(),
        }

        self.guard_manager.finalize()

        globals_for_guard_fn = {"G": builder.scope["G"]}
        # Guard manager construction is complete. Ensure we did not miss to
        # insert a guard in cpp guard manager.
        assert len(code_parts) == 0

        self.guard_manager.closure_vars = closure_vars
        self.guard_manager.args = largs
        self.guard_manager.populate_code_parts_for_debugging()
        self.guard_manager.verbose_code_parts = verbose_code_parts
        # Grab only G, but preserve "G" because guards access it as "G"
        self.guard_manager.global_scope = globals_for_guard_fn
        self.guard_manager.guard_fail_fn = guard_fail_fn
        # will be populated by a non-owning reference to CacheEntry/ExtraState
        # when the CacheEntry is constructed
        self.guard_manager.cache_entry = None
        self.guard_manager.extra_state = None
        self.guard_manager.no_tensor_aliasing_sources = no_tensor_aliasing_names