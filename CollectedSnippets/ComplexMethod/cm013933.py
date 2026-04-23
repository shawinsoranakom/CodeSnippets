def __init__(
        self,
        f_code: types.CodeType,
        output_graph: OutputGraphCommon,
        cache_entry: CacheEntry | None = None,
        guard_fail_fn: Callable[[GuardFail], None] | None = None,
        guard_filter_fn: Callable[[Sequence[GuardFilterEntry]], Sequence[bool]]
        | None = None,
        shape_code_parts: ShapeCodeParts | None = None,
        runtime_global_scope: dict[str, Any] | None = None,
        save_guards: bool = False,
        strict_error: bool = False,
    ) -> None:
        guards = output_graph.guards if output_graph else None
        self._weakrefs: dict[int, ReferenceType[object]] = {}

        existing_diff_guard_sources = (
            update_diff_guard_managers_for_existing_cache_entries(cache_entry)
        )
        self.output_graph: OutputGraphCommon | None = output_graph
        assert self.output_graph is not None

        # Only used for serialization.
        self.shape_code_parts = shape_code_parts

        # NB: Until we trace device contexts, we need to use the stack recorded at the beginning of tracing
        # in case a set default device call was made in the graph.
        self.torch_function_mode_stack = (
            output_graph.torch_function_mode_stack if output_graph else None
        )
        self.used_builtin_vars: OrderedSet[str] = OrderedSet()
        self.additional_used_local_vars: OrderedSet[str] = OrderedSet()
        self.additional_used_global_vars: OrderedSet[str] = OrderedSet()
        self.runtime_global_scope = runtime_global_scope
        self.global_state: torch._C._dynamo.guards.GlobalStateGuard | None = None
        self.torch_function_mode_stack_check_fn: Callable[[], bool] | None = None

        if not justknobs_check("pytorch/compiler:guard_nn_modules"):
            log.warning("guard_nn_modules is turned off using justknobs killswitch")

        # TODO Be more explicit about the behavior for the users.
        if torch._dynamo.config.caching_precompile:
            _guard_filter_fn = guard_filter_fn or (lambda gs: [True for g in gs])

            def guard_filter_fn(guards: Sequence[GuardFilterEntry]) -> Sequence[bool]:
                ret = []
                for keep, g in zip(_guard_filter_fn(guards), guards):
                    if not keep:
                        ret.append(False)
                    elif (
                        g.guard_type
                        in (
                            "ID_MATCH",
                            "CLOSURE_MATCH",
                            "WEAKREF_ALIVE",
                            "DICT_VERSION",
                        )
                        or "ID_MATCH" in g.derived_guard_types
                        or "DICT_VERSION" in g.derived_guard_types
                    ):
                        log.warning(
                            "%s guard on %s is dropped with caching_precompile=True.",
                            g.guard_type,
                            g.orig_guard.name,
                        )
                        ret.append(False)
                    else:
                        ret.append(True)
                return ret

        sorted_guards = sorted(guards or (), key=Guard.sort_key)

        # Disable __torch_function__ dispatch during guard construction so
        # modes with mutable state aren't triggered.  We exit the context
        # before the guard sanity check so GlobalStateGuard.check() sees
        # the true runtime state.
        with torch._C.DisableTorchFunction():
            if guard_filter_fn:
                # If we're filtering guards, we need to build it an extra time first
                # because filtering depends on the builder/guard_manager results
                builder, guard_manager = self.build_guards(
                    sorted_guards,
                    existing_diff_guard_sources,
                    f_code,
                    output_graph,
                    False,
                )

                filter_results = guard_filter_fn(
                    [make_guard_filter_entry(guard, builder) for guard in sorted_guards]
                )
                assert len(filter_results) == len(sorted_guards)
                assert all(type(x) is bool for x in filter_results)
                sorted_guards = [
                    guard for i, guard in enumerate(sorted_guards) if filter_results[i]
                ]

            # Redo the guards because filtering relies on the results from the last guard builder.
            builder, guard_manager = self.build_guards(
                sorted_guards,
                existing_diff_guard_sources,
                f_code,
                output_graph,
                save_guards,
                guard_filter_fn=guard_filter_fn,
            )

            self.guard_manager = guard_manager
            self.compile_check_fn(builder, sorted_guards, guard_fail_fn)

        # Keep track of weak references of objects with ID_MATCH guard. This
        # info is stored alongside optimized_code and guard_manager and is used to
        # limit the number of cache entries with same ID_MATCH'd object.
        # TODO(anijain2305) - Currently this information is stored as an attr on
        # the guard_manager itself to avoid changing CacheEntry data structure in
        # eval_frame.c. In future, we should probably replace guard_manager with a
        # queryable data structure such that this information is already present
        # in some form.
        self.guard_manager.id_matched_objs = builder.id_matched_objs

        guards_log.debug("%s", self.guard_manager)
        self.guard_manager.id_matched_objs = builder.id_matched_objs

        # Check that the guard returns True. False means that we will always
        # recompile.
        # TODO(anijain2305, ydwu4) - Skipping export because of following test
        # python -s test/dynamo/test_export.py -k test_export_with_symbool_inputs
        latency = 0.0

        if not output_graph.skip_guards_check and not output_graph.export:
            if not self.guard_manager.check(output_graph.local_scope):
                reasons = get_guard_fail_reason_helper(
                    self.guard_manager,
                    output_graph.local_scope,
                    CompileContext.current_compile_id(),
                    backend=None,  # no need to set this because we are trying to find the offending guard entry
                )
                raise AssertionError(
                    "Guard failed on the same frame it was created. This is a bug - please create an issue."
                    f"Guard fail reason: {reasons}"
                )

            if guard_manager_testing_hook_fn is not None:
                guard_manager_testing_hook_fn(
                    self.guard_manager, output_graph.local_scope, builder
                )

            # NB for developers: n_iters is chosen to be 1 to prevent excessive
            # increase in compile time. We first do a cache flush to measure the
            # guard latency more accurately. This cache flush is expensive.
            # Note  - If you are working on a guard optimization, it might be a
            # good idea to increase this number for more stability during
            # development.
            latency = profile_guard_manager(
                self.guard_manager.root, output_graph.local_scope, 1
            )
            guards_log.debug("Guard eval latency = %s us", f"{latency:.2f}")
            # Note: We use `increment_toplevel` instead of `compilation_metric`
            # here.  This is because, in scenarios where `torch._dynamo.reset`
            # is invoked, the same frame ID and compile ID may be reused during
            # a new compilation cycle.  This behavior causes issues with
            # `compilation_metric`, as it expects the metric field to be empty.
            # Ideally, we would overwrite the existing entry in such cases, but
            # we currently lack an API to support overwriting metrics.  However,
            # since these situations are rare and typically impractical to
            # account for, we simply increment at the toplevel instead.
            CompileEventLogger.increment_toplevel("guard_latency_us", int(latency))

        self.guards_state: bytes | None = None
        if save_guards:
            from torch._dynamo.output_graph import OutputGraphCommon

            assert isinstance(self.output_graph, OutputGraphCommon)
            try:
                self.guards_state = self.serialize_guards(
                    builder, sorted_guards, self.output_graph
                )
            except exc.PackageError as e:
                if torch._dynamo.config.strict_precompile or strict_error:
                    raise e
                self.output_graph.bypass_package(
                    f"Guard evaluation failed: {str(e)}",
                    traceback=traceback.format_exc().split("\n"),
                )

        # TODO: don't do the string rep, do something more structured here
        torch._logging.trace_structured(
            "dynamo_cpp_guards_str",
            payload_fn=lambda: f"{self.guard_manager}\nGuard latency = {latency:.2f} us",
        )
        # NB - We have to very careful of cleaning up here. Because of the
        # invalidate function, we can create a weakref finalizer that keeps
        # `self` alive for very long. Sometimes by mistake, we can run
        # invalidate for a type/object (check id_ref method) that Python can
        # leak by design, preventing us from calling the finalizer. In that
        # case, the `self` will be alive even though the cache entry will be
        # deleted (check invalidate method), which can cause a memory leak,
        # e.g., not setting output_graph = None can keep hold of nn_modules.
        self._weakrefs.clear()
        self.output_graph = None