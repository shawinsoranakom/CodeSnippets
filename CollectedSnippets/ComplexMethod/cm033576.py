def run_test(data: dict[str, t.Any]) -> t.Any:
        nonlocal expected_value

        secondary_templar = TemplateEngine()

        # Run under a secondary context using a templar with no variables; this allows us to test the correct propagation and use of the
        # embedded templar in lazy containers. Templated values will not render correctly if they pick up the ambient (no-vars) templar during
        # various copy/operator scenarios.
        with TemplateContext(template_value='', templar=secondary_templar, options=TemplateOptions.DEFAULT, stop_on_template=False):
            code_globals = dict(
                copy=copy,
                ExampleSingletonTag=ExampleSingletonTag,
            )

            try:
                result = eval(expression, code_globals, data)
            except SyntaxError:
                # some expressions use a semicolon to force exec instead of eval, even if they only need a single statement
                exec(expression, code_globals, data)

                var_name = list(expected_value)[0]
                expected_value = expected_value[var_name]
                result = data[var_name]
            except Exception as ex:
                if type(ex) is not expected_type:  # pylint: disable=unidiomatic-typecheck
                    # we weren't expecting an exception, or got one of the wrong type; re-raise it now for the traceback instead of just a failed assertion
                    raise

                result = ex

        assert type(result) is expected_type  # pylint: disable=unidiomatic-typecheck

        expected_result: t.Any  # avoid type narrowing

        if issubclass(expected_type, list):
            assert isinstance(result, list)  # redundant, but assists mypy in understanding the type

            expected_list_types = [type(value) for value in expected_value]
            expected_result = [value.value if isinstance(value, _LazyValue) else value for value in expected_value]

            actual_list_types: list[type] = [type(value) for value in list.__iter__(result)]

            assert actual_list_types == expected_list_types
        elif issubclass(expected_type, tuple):
            assert isinstance(result, tuple)  # redundant, but assists mypy in understanding the type

            expected_tuple_types = [type(value) for value in expected_value]
            expected_result = expected_value

            actual_tuple_types: list[type] = [type(value) for value in tuple.__iter__(result)]

            assert actual_tuple_types == expected_tuple_types
        elif issubclass(expected_type, dict):
            assert isinstance(result, dict)  # redundant, but assists mypy in understanding the type

            expected_dict_types = {key: type(value) for key, value in expected_value.items()}
            expected_result = {key: value.value if isinstance(value, _LazyValue) else value for key, value in expected_value.items()}

            actual_dict_types: dict[str, type] = {key: type(value) for key, value in dict.items(result)}

            assert actual_dict_types == expected_dict_types
        elif issubclass(expected_type, Exception):
            result = str(result)  # unfortunately exceptions can't be compared for equality, so use the string representation instead
            expected_result = expected_value
        else:
            expected_result = expected_value

        assert result == expected_result