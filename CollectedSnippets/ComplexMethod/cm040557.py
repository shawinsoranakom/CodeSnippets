def test_class_function_consistency(self, module_name):
        ops_module = getattr(ops, module_name)
        if module_name in ("core", "math"):
            # `core` and `math` are not exported as their own module.
            api_ops_module = None
        else:
            api_ops_module = getattr(api_ops_root, module_name)

        for op_function, op_class in op_functions_and_classes(ops_module):
            name = op_function.__name__

            # ==== Check exports ====
            # - op should be exported as e.g. `keras.ops.numpy.sum`
            # - op should also be exported as e.g. `keras.ops.sum`

            if module_name != "image":
                # `image` ops are not exported at the top-level.
                self.assertIsNotNone(
                    getattr(api_ops_root, name, None),
                    f"Not exported as `keras.ops.{name}`",
                )
            if api_ops_module is not None:
                # `core` and `math` are not exported as their own module.
                self.assertIsNotNone(
                    getattr(api_ops_module, name, None),
                    f"Not exported as `keras.ops.{module_name}.{name}`",
                )

            # ==== Check handling of name in __init__ ====
            # - op class `__init__` should have a `name` parameter at the end,
            #   which should be keyword only and with a default value of `None`
            # - op class `__init__` should call `super().__init__(name=name)`

            if op_class.__init__ is Operation.__init__:
                # `name` is not keyword only in `Operation`, use this instead.
                class_init_signature = inspect.Signature(
                    [SELF_PARAMETER, NAME_PARAMETER]
                )
            else:
                class_init_signature = inspect.signature(op_class.__init__)

                # Check call to super.
                self.assertContainsSubsequence(
                    inspect.getsource(op_class.__init__),
                    "super().__init__(name=name)",
                    f"`{op_class.__name__}.__init__` is not calling "
                    "`super().__init__(name=name)`",
                )

            static_parameters = list(class_init_signature.parameters.values())
            # Remove `self`.
            static_parameters = static_parameters[1:]
            name_index = -1
            if static_parameters[-1].kind == inspect.Parameter.VAR_KEYWORD:
                # When there is a `**kwargs`, `name` appears before.
                name_index = -2
            # Verify `name` parameter is as expected.
            self.assertEqual(
                static_parameters[name_index],
                NAME_PARAMETER,
                f"The last parameter of `{op_class.__name__}.__init__` "
                "should be `name`, should be a keyword only, and should "
                "have a default value of `None`",
            )
            # Remove `name`, it's not part of the op signature.
            static_parameters.pop(name_index)

            # ==== Check static parameters ====
            # Static parameters are declared in the class' `__init__`.
            # Dynamic parameters are declared in the class' `call` method.
            # - they should all appear in the op signature with the same name
            # - they should have the same default value
            # - they should appear in the same order and usually with the
            #   dynamic parameters first, and the static parameters last.

            dynamic_parameters = list(
                inspect.signature(op_class.call).parameters.values()
            )[1:]  # Remove self

            op_signature = inspect.signature(op_function)

            for p in dynamic_parameters + static_parameters:
                # Check the same name appears in the op signature
                self.assertIn(
                    p.name,
                    op_signature.parameters,
                    f"Op function `{name}` is missing a parameter that is in "
                    f"op class `{op_class.__name__}`",
                )
                # Check default values are the same
                self.assertEqual(
                    p.default,
                    op_signature.parameters[p.name].default,
                    f"Default mismatch for parameter `{p.name}` between op "
                    f"function `{name}` and op class `{op_class.__name__}`",
                )

            dynamic_parameter_names = [p.name for p in dynamic_parameters]
            static_parameter_names = [p.name for p in static_parameters]

            # Check for obvious mistakes in parameters that were made dynamic
            # but should be static.
            for p in dynamic_parameters:
                self.assertNotIn(
                    p.name,
                    STATIC_PARAMETER_NAMES,
                    f"`{p.name}` should not be a dynamic parameter in op class "
                    f"`{op_class.__name__}` based on its name.",
                )
                self.assertNotIsInstance(
                    p.default,
                    (bool, str),
                    f"`{p.name}` should not be a dynamic parameter in op class "
                    f"`{op_class.__name__}` based on default `{p.default}`.",
                )

            # Check order of parameters.
            if name in (
                "fori_loop",
                "vectorized_map",
                "while_loop",
                "batch_normalization",
                "dot_product_attention",
                "average",
                "einsum",
                "full",
                "pad",
            ):
                # Loose case:
                # order of of parameters is preserved but they are interspersed.
                op_dynamic_parameter_names = [
                    name
                    for name in op_signature.parameters.keys()
                    if name in dynamic_parameter_names
                ]
                self.assertEqual(
                    op_dynamic_parameter_names,
                    dynamic_parameter_names,
                    "Inconsistent dynamic parameter order for op "
                    f"function `{name}` and op class `{op_class.__name__}`",
                )
                op_static_parameter_names = [
                    name
                    for name in op_signature.parameters.keys()
                    if name in static_parameter_names
                ]
                self.assertEqual(
                    op_static_parameter_names,
                    static_parameter_names,
                    "Inconsistent static parameter order for op "
                    f"function `{name}` and op class `{op_class.__name__}`",
                )
            else:
                # Strict case:
                # dynamic parameters first and static parameters at the end.
                self.assertEqual(
                    list(op_signature.parameters.keys()),
                    dynamic_parameter_names + static_parameter_names,
                    "Inconsistent static parameter position for op "
                    f"function `{name}` and op class `{op_class.__name__}`",
                )

            # ==== Check compute_output_spec is implement ====
            # - op class should override Operation's `compute_output_spec`
            self.assertTrue(
                hasattr(op_class, "compute_output_spec")
                and op_class.compute_output_spec
                is not Operation.compute_output_spec,
                f"Op class `{op_class.__name__}` should override "
                "`compute_output_spec`",
            )