def solve(goal: NamedCType, *, direct: bool) -> str:
        def direct_solve(goal: NamedCType) -> str:
            return solve(goal, direct=True)

        if goal in ctx:
            # Trivial
            return ctx[goal]

        # const & is satisfied with mutable &
        if isinstance(goal.type, ConstRefCType):
            try:
                # WARNING: not strictly decreasing; be careful not
                # to add a direct conversion that goes satisfies
                # mutable& with const&
                return solve(
                    NamedCType(goal.name, MutRefCType(goal.type.elem)), direct=direct
                )
            except UnsatError:
                pass

        # mutable & is satisfied with value
        if isinstance(goal.type, MutRefCType):
            try:
                return solve(NamedCType(goal.name, goal.type.elem), direct=direct)
            except UnsatError:
                pass

        # TODO: These are referentially equal, shouldn't have to do this;
        # ensuring we don't use type synonym IntArrayRef in codegen would
        # help
        if goal.type == ArrayRefCType(BaseCType(longT)):
            return solve(NamedCType(goal.name, BaseCType(intArrayRefT)), direct=direct)

        if direct:
            unsat(goal)

        # For now, all of these rules are mutually exclusive.
        if goal == NamedCType("memory_format", OptionalCType(BaseCType(memoryFormatT))):
            memory_format = direct_solve(
                NamedCType(
                    SpecialArgName.possibly_redundant_memory_format,
                    OptionalCType(BaseCType(memoryFormatT)),
                )
            )
            # No need to join "memory_format" and "options" if the target API takes "options" directly.
            # Otherwise it will cause the redundant memory_format error.
            if options_ctype in goal_ctypes:
                return memory_format
            try:
                options = direct_solve(options_ctype)
                return f"c10::impl::check_tensor_options_and_extract_memory_format({options}, {memory_format})"
            except UnsatError:
                return memory_format
        elif goal == NamedCType("options", BaseCType(tensorOptionsT)):
            dtype = direct_solve(
                NamedCType("dtype", OptionalCType(BaseCType(scalarTypeT)))
            )
            pin_memory = direct_solve(
                NamedCType("pin_memory", OptionalCType(BaseCType(boolT)))
            )
            device = direct_solve(
                NamedCType("device", OptionalCType(BaseCType(deviceT)))
            )
            layout = direct_solve(
                NamedCType("layout", OptionalCType(BaseCType(layoutT)))
            )
            return f"TensorOptions().dtype({dtype}).layout({layout}).device({device}).pinned_memory({pin_memory})"

        elif goal == NamedCType("dtype", OptionalCType(BaseCType(scalarTypeT))):
            try:
                options = direct_solve(options_ctype)
                return f"c10::optTypeMetaToScalarType({options}.dtype_opt())"
            except UnsatError:
                out_tensor = direct_solve(out_tensor_ctype)
                return f"{out_tensor}.scalar_type()"

        elif goal == NamedCType("layout", OptionalCType(BaseCType(layoutT))):
            try:
                options = direct_solve(options_ctype)
                return f"{options}.layout_opt()"
            except UnsatError:
                out_tensor = direct_solve(out_tensor_ctype)
                return f"{out_tensor}.layout()"

        elif goal == NamedCType("device", OptionalCType(BaseCType(deviceT))):
            try:
                options = direct_solve(options_ctype)
                return f"{options}.device_opt()"
            except UnsatError:
                out_tensor = direct_solve(out_tensor_ctype)
                return f"{out_tensor}.device()"

        elif goal == NamedCType("pin_memory", OptionalCType(BaseCType(boolT))):
            try:
                options = direct_solve(options_ctype)
                return f"{options}.pinned_memory_opt()"
            except UnsatError:
                # If we're calling a factory op from its out= variant,
                # We don't actually care about the value of pin_memory.
                out_tensor = direct_solve(out_tensor_ctype)
                return "::std::nullopt"

        # We can always do translations from value types to reference types, like vector<int> -> IntArrayRef
        elif goal.type == BaseCType(intArrayRefT):
            try:
                return direct_solve(NamedCType(goal.name, longVec_ctype))
            except UnsatError:
                # We can also go SymIntArrayRef -> IntArrayRef
                symIntArrayRef_type = direct_solve(
                    NamedCType(goal.name, BaseCType(symIntArrayRefT))
                )
                return f"C10_AS_INTARRAYREF_SLOW({symIntArrayRef_type})"
        elif goal.type == BaseCType(symIntArrayRefT):
            try:
                r = direct_solve(NamedCType(goal.name, BaseCType(intArrayRefT)))
                return f"c10::fromIntArrayRefSlow({r})"
            except UnsatError:
                return direct_solve(NamedCType(goal.name, longSymVec_ctype))
        elif goal.type == BaseCType(SymIntT):
            return direct_solve(NamedCType(goal.name, BaseCType(longT)))
        elif goal.type == OptionalCType(BaseCType(SymIntT)):
            argname = direct_solve(
                NamedCType(goal.name, OptionalCType(BaseCType(longT)))
            )
            return f"{argname}.has_value() ? ::std::make_optional(c10::SymInt(*{argname})) : ::std::nullopt"
        elif goal.type == BaseCType(longT):
            symInt_type = direct_solve(NamedCType(goal.name, BaseCType(SymIntT)))
            return f"{symInt_type}.guard_int(__FILE__, __LINE__)"
        elif goal.type == OptionalCType(BaseCType(longT)):
            argname = direct_solve(
                NamedCType(goal.name, OptionalCType(BaseCType(SymIntT)))
            )
            return f"{argname}.has_value() ? ::std::make_optional({argname}->guard_int(__FILE__, __LINE__)) : ::std::nullopt"
        elif goal.type == BaseCType(optionalIntArrayRefT):
            try:
                return direct_solve(NamedCType(goal.name, optionalLongVec_ctype))
            except UnsatError:
                argname = direct_solve(
                    NamedCType(goal.name, BaseCType(optionalSymIntArrayRefT))
                )
                return f"{argname}.has_value() ? ::std::make_optional(C10_AS_INTARRAYREF_SLOW(*{argname})) : ::std::nullopt"
        elif goal.type == BaseCType(optionalSymIntArrayRefT):
            # TODO: You might also want to solve this from longSymVec_ctype or
            # an optional version of it
            argname = direct_solve(
                NamedCType(goal.name, BaseCType(optionalIntArrayRefT))
            )
            return f"{argname}.has_value() ? ::std::make_optional(c10::fromIntArrayRefSlow(*{argname})) : ::std::nullopt"
        elif goal.type == BaseCType(optionalScalarRefT):
            return direct_solve(NamedCType(goal.name, optionalScalar_ctype))
        elif goal.type == BaseCType(optionalTensorRefT):
            return direct_solve(NamedCType(goal.name, optionalTensor_ctype))

        # Note [translation from C++ reference to value types]
        # The below cases are all for when we have an argument with a reference type,
        # and a corresponding goal with a value type.
        # These are needed when we populate the inputs to a lambda capture and we need
        # to guarantee the lifetime of each captured argument.
        # We guard it with an explicit kwarg because converting to a value type is expensive
        # (O(n)) to convert from IntArrayRef to vector<int>),
        # so the caller of translate() should be explicit that they need it.
        if allow_expensive_conversions:
            if goal.type == VectorCType(BaseCType(longT)):
                intArrayRef_ctype = NamedCType(goal.name, BaseCType(intArrayRefT))
                argname = direct_solve(intArrayRef_ctype)
                return f"{argname}.vec()"
            if goal.type == VectorCType(BaseCType(SymIntT)):
                symIntArrayRef_ctype = NamedCType(goal.name, BaseCType(symIntArrayRefT))
                argname = direct_solve(symIntArrayRef_ctype)
                return f"{argname}.vec()"
            elif goal.type == OptionalCType(VectorCType(BaseCType(longT))):
                optionalIntArrayRef_ctype = NamedCType(
                    goal.name, BaseCType(optionalIntArrayRefT)
                )
                argname = direct_solve(optionalIntArrayRef_ctype)
                return f"{argname}.has_value() ? ::std::make_optional({argname}->vec()) : ::std::nullopt"
            elif goal.type == OptionalCType(BaseCType(scalarT)):
                optionalScalarRef_ctype = NamedCType(
                    goal.name, BaseCType(optionalScalarRefT)
                )
                argname = direct_solve(optionalScalarRef_ctype)
                return f"{argname}.has_value() ? ::std::make_optional({argname}) : ::std::nullopt"
            elif goal.type == OptionalCType(BaseCType(scalarT)):
                optionalTensorRef_ctype = NamedCType(
                    goal.name, BaseCType(optionalTensorRefT)
                )
                argname = direct_solve(optionalTensorRef_ctype)
                return f"{argname}.has_value() ? ::std::make_optional({argname}) : ::std::nullopt"
            # Technically, we also need to handle cases of C++ containers holding reference types.
            # But there currently aren't any ops that require lambda capture codegen
            # With arguments like ::std::vector<IntArrayRef>.
            # If that changes, we'll have to add the translation here.

        # We allow const casting on tensors, since const-correctness is a bit broken for at::Tensor.
        # We could probably generalize this to non-tensor types too.
        if goal.type == MutRefCType(BaseCType(tensorT)):
            const_ref_tensor_ctype = NamedCType(
                goal.name, ConstRefCType(BaseCType(tensorT))
            )
            argname = direct_solve(const_ref_tensor_ctype)
            return f"const_cast<Tensor&>({argname})"

        unsat(goal)