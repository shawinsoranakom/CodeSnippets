def _set_guard_export_info(
        self,
        guard: Guard,
        code_list: list[str],
        provided_guarded_object: Any | None = None,
        provided_func_name: str | None = None,
    ) -> None:
        # WARNING: It is important that cur_frame/caller do NOT stay in
        # the current frame, because they will keep things live longer
        # than they should.  See TestMisc.test_release_module_memory
        cur_frame = currentframe()
        assert cur_frame is not None
        caller = cur_frame.f_back
        del cur_frame
        assert caller is not None
        func_name = provided_func_name or caller.f_code.co_name
        del caller
        # We use func_name for export, so might as well get a nice defensive check out of it
        assert func_name in self.__class__.__dict__, (
            f"_produce_guard_code must be called from inside GuardedCode. Called from {func_name}"
        )

        # Not all guards have names, some can be installed globally (see asserts on HAS_GRAD)
        if provided_guarded_object is None:
            name = guard.name
            guarded_object = None if not name else self.get(guard)
        else:
            guarded_object = provided_guarded_object

        guarded_object_type = (
            weakref.ref(type(guarded_object)) if guarded_object is not None else None
        )
        obj_ref = None
        # Not necessary to have weakref for Enum type, but there is a bug that
        # makes hasattr(guarded_object.__class__, "__weakref__") return True.
        supports_weakref = (
            getattr(guarded_object.__class__, "__weakrefoffset__", 0) != 0
        )
        # See D64140537 for why we are checking for tuple.
        if supports_weakref and not isinstance(
            guarded_object, (enum.Enum, tuple, weakref.ProxyTypes)
        ):
            obj_ref = weakref.ref(guarded_object)

        guard.set_export_info(
            func_name,
            guarded_object_type,
            code_list,
            obj_ref,
        )