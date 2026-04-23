def EQUALS_MATCH(self, guard: Guard, recompile_hint: str | None = None) -> None:
        ref = self.arg_ref(guard)
        val = self.get(guard)
        if np:
            np_types: tuple[type[Any], ...] = (
                np.int8,
                np.int16,
                np.int32,
                np.int64,
                np.uint8,
                np.uint16,
                np.uint32,
                np.uint64,
                np.float16,
                np.float32,
                np.float64,
            )
        else:
            np_types = ()

        ok_mutable_types = (list, set)

        ok_types = tuple(
            common_constant_types
            | {
                type,
                tuple,
                frozenset,
                slice,
                range,
                dict_keys,
                torch.Size,
                torch.Stream,
                torch.cuda.streams.Stream,
                *np_types,
                *ok_mutable_types,
            }
        )

        if torch.distributed.is_available():
            from torch.distributed.device_mesh import _MeshLayout, DeviceMesh
            from torch.distributed.tensor.placement_types import (
                _StridedShard,
                Partial,
                Replicate,
                Shard,
            )

            ok_types = ok_types + (
                Shard,
                Replicate,
                Partial,
                DeviceMesh,
                _StridedShard,
                _MeshLayout,
            )

        from torch.export.dynamic_shapes import _IntWrapper

        ok_types = ok_types + (_IntWrapper,)

        import torch.utils._pytree as pytree

        assert (
            isinstance(val, ok_types)
            or pytree.is_constant_class(type(val))
            or is_opaque_value_type(type(val))
        ), f"Unexpected type {type(val)}"

        # Special case for nan because float("nan") == float("nan") evaluates to False
        if istype(val, float) and math.isnan(val):
            code = [f"(type({ref}) is float and __math_isnan({ref}))"]
            self._set_guard_export_info(guard, code)

            self.get_guard_manager(guard).add_float_is_nan_guard(
                get_verbose_code_parts(code, guard),
                guard.user_stack,
            )
            return

        # Python math library doesn't support complex nan, so we need to use numpy
        # pyrefly: ignore [missing-attribute]
        if istype(val, complex) and np.isnan(val):
            code = [f"(type({ref}) is complex and __numpy_isnan({ref}))"]
            self._set_guard_export_info(guard, code)

            self.get_guard_manager(guard).add_complex_is_nan_guard(
                get_verbose_code_parts(code, guard),
                guard.user_stack,
            )
            return

        # Construct a debug string to put into the c++ equals match guard.
        code = [f"{ref} == {val!r}"]
        if istype(val, ok_mutable_types):
            # C++ guards perform a pointer equality check to speedup guards, but the assumption is that the object
            # is immutable. For a few corner cases like sets and lists, we make a deepcopy to purposefully fail the
            # pointer equality check.
            val = deepcopy(val)

        verbose_code_parts = get_verbose_code_parts(code, guard)
        if recompile_hint:
            verbose_code_parts = [
                f"{part} (HINT: {recompile_hint})" for part in verbose_code_parts
            ]

        self.get_guard_manager(guard).add_equals_match_guard(
            val, verbose_code_parts, guard.user_stack
        )
        self._set_guard_export_info(guard, code)
        return