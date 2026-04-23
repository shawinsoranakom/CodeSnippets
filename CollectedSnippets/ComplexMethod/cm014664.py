def test_aligned_public_apis(self):
        public_apis = python_pytree.__all__

        self.assertEqual(public_apis, cxx_pytree.__all__)

        for name in public_apis:
            cxx_api = getattr(cxx_pytree, name)
            python_api = getattr(python_pytree, name)

            self.assertEqual(inspect.isclass(cxx_api), inspect.isclass(python_api))
            self.assertEqual(
                inspect.isfunction(cxx_api),
                inspect.isfunction(python_api),
            )
            if inspect.isfunction(cxx_api):
                cxx_signature = inspect.signature(cxx_api)
                python_signature = inspect.signature(python_api)

                # Check the parameter names are the same.
                cxx_param_names = list(cxx_signature.parameters)
                python_param_names = list(python_signature.parameters)
                self.assertEqual(cxx_param_names, python_param_names)

                # Check the positional parameters are the same.
                cxx_positional_param_names = [
                    n
                    for n, p in cxx_signature.parameters.items()
                    if (
                        p.kind
                        in {
                            inspect.Parameter.POSITIONAL_ONLY,
                            inspect.Parameter.POSITIONAL_OR_KEYWORD,
                        }
                    )
                ]
                python_positional_param_names = [
                    n
                    for n, p in python_signature.parameters.items()
                    if (
                        p.kind
                        in {
                            inspect.Parameter.POSITIONAL_ONLY,
                            inspect.Parameter.POSITIONAL_OR_KEYWORD,
                        }
                    )
                ]
                self.assertEqual(
                    cxx_positional_param_names,
                    python_positional_param_names,
                )

                for python_name, python_param in python_signature.parameters.items():
                    self.assertIn(python_name, cxx_signature.parameters)
                    cxx_param = cxx_signature.parameters[python_name]

                    # Check parameter kinds and default values are the same.
                    self.assertEqual(cxx_param.kind, python_param.kind)
                    self.assertEqual(cxx_param.default, python_param.default)

                    # Check parameter annotations are the same.
                    if "TreeSpec" in str(cxx_param.annotation):
                        self.assertIn("TreeSpec", str(python_param.annotation))
                        self.assertEqual(
                            re.sub(
                                r"(?:\b)([\w\.]*)TreeSpec(?:\b)",
                                "TreeSpec",
                                str(cxx_param.annotation),
                            ),
                            re.sub(
                                r"(?:\b)([\w\.]*)TreeSpec(?:\b)",
                                "TreeSpec",
                                str(python_param.annotation),
                            ),
                            msg=(
                                f"C++ parameter {cxx_param} "
                                f"does not match Python parameter {python_param} "
                                f"for API `{name}`"
                            ),
                        )
                    else:
                        self.assertEqual(
                            cxx_param.annotation,
                            python_param.annotation,
                            msg=(
                                f"C++ parameter {cxx_param} "
                                f"does not match Python parameter {python_param} "
                                f"for API `{name}`"
                            ),
                        )