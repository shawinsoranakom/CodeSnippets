def test_generator(func, override):
        # If func corresponds to a torch.Tensor method or property.
        if is_tensor_method_or_property(func):
            # Generate an instance by using SubTensor,
            def instance_gen():
                return SubTensor([5])
        else:
            # Otherwise, TensorLike.
            def instance_gen():
                return TensorLike()

        # FIXME The following code does not support kwonly args without defaults.
        # The fix is easy, as one just needs to save these args when generating the variable
        # annotated_args. The problem is that, if one does so, one finds a number
        # of functions that have problematic signatures in native_functions.yaml.
        # Fixing these would be BC breaking, so hence this terrible hack
        # https://github.com/pytorch/pytorch/issues/67008
        kwargs = {}
        if hasattr(func, "__name__") and "linalg_solve_triangular" in func.__name__:
            kwargs = {"upper": True}

        func_args = []
        is_method = is_tensor_method_or_property(func)

        def _simple_type_parser(func, arg_name, arg_type):
            # Guess valid input to aten function based on type of argument
            if arg_type == "Tensor":
                return instance_gen()
            elif arg_type == "TensorList" or arg_type == "ITensorListRef":
                return [instance_gen(), instance_gen()]
            elif arg_type == "c10::List<::std::optional<Tensor>>":
                return [instance_gen(), instance_gen()]
            elif arg_type == "IntArrayRef" or arg_type == "SymIntArrayRef":
                size = arg.get("size", 2)
                if size == 1:
                    return 1
                else:
                    return [1] * size
            elif arg_type == "Scalar":
                return 3.5
            elif arg_type == "bool":
                return False
            elif arg_type == "Dimname":
                return ""
            elif arg_type == "DimnameList":
                return [""]
            elif arg_type.startswith("int"):
                return 0
            elif arg_type == "Stream":
                return torch.Stream()
            elif arg_type.startswith("float") or arg_type == "double":
                return 1.0
            elif arg_type in {"Generator", "MemoryFormat", "TensorOptions"}:
                return None
            elif arg_type == "ScalarType":
                return torch.float32
            elif arg_type == "c10::string_view":
                return ""
            elif arg_type in ("std::string_view", "::std::string_view"):
                return ""
            elif arg_type == "SymInt":
                # TODO: generate actual SymbolicInt
                return 1
            else:
                raise RuntimeError(
                    f"Unsupported argument type {arg_type} for {arg_name} of function {func}"
                )

        # Special case; this doesn't have a schema but takes a list
        if func is torch.sym_sum:
            func_args.append([TensorLike(), TensorLike()])
        elif func in annotated_args:
            for arg in annotated_args[func]:
                # Guess valid input to aten function based on type of argument
                t = arg["simple_type"]
                t = t.removesuffix("?")
                if t == "Tensor" and is_method and arg["name"] == "self":
                    # See "Note: properties and __get__"
                    func = func.__get__(instance_gen())
                    continue
                arg_to_add = _simple_type_parser(func, arg["name"], t)
                if "is_kwarg_only" in arg and arg["is_kwarg_only"] == str(True):
                    kwargs[arg["name"]] = arg_to_add
                else:
                    func_args.append(arg_to_add)
        else:
            args = inspect.getfullargspec(override)
            try:
                func_args = inspect.getfullargspec(func)
                # Remove annotations from argspec
                func_args = type(func_args)(**{**func_args, 'annotations': None})
                if func_args != args:
                    raise RuntimeError(f"Override for {func} doesn't match its argspec.\n"
                                       + f"Original: {inspect.signature(func)}\n"
                                       + f"Override: {inspect.signature(override)}")
            except TypeError:
                pass
            nargs = len(args.args)
            if args.defaults is not None:
                nargs -= len(args.defaults)
            func_args = [instance_gen() for _ in range(nargs)]
            if args.varargs is not None:
                func_args += [instance_gen(), instance_gen()]

        def test(self):
            ret = func(*func_args, **kwargs)
            # ret is None for certain protocols, e.g., `__weakref__` and `__setitem__`
            # This is currently the best check but doesn't work for, for example,
            # Tensor.__add__ because it redirects to Tensor.add.
            # See note "_triggered wrapper"
            if not is_method or ret is None:
                self.assertTrue(WRAPPED_TRIGGERED_IMPLS[func]._triggered)
                return

            self.assertEqual(ret, -1)

        return test