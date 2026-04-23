def construct_method(attr, prefix, tester):
        method = getattr(testcase, attr)
        if getattr(method, "_torch_dont_generate_opcheck_tests", False):
            return
        new_method_name = prefix + "__" + attr

        @functools.wraps(method)
        def new_method(*args, **kwargs):
            with OpCheckMode(
                namespaces,
                prefix,
                tester,
                failures_dict,
                f"{testcase.__name__}.{new_method_name}",
                failures_dict_path,
            ):
                result = method(*args, **kwargs)
            return result

        if pytestmark := new_method.__dict__.get("pytestmark"):
            import pytest

            # check if we need to simplify the parametrize marks
            # NB: you need to add this mark to your pytest.ini
            opcheck_only_one = False
            for mark in pytestmark:
                if isinstance(mark, pytest.Mark) and mark.name == "opcheck_only_one":
                    opcheck_only_one = True

            if opcheck_only_one:
                new_pytestmark = []
                for mark in pytestmark:
                    if isinstance(mark, pytest.Mark) and mark.name == "parametrize":
                        argnames, argvalues = mark.args
                        if mark.kwargs:
                            raise AssertionError("NYI: mark.kwargs is not empty")
                        # Special case for device, we want to run on all
                        # devices
                        if argnames != "device":
                            new_pytestmark.append(
                                pytest.mark.parametrize(
                                    argnames, (next(iter(argvalues)),)
                                )
                            )
                            continue
                    new_pytestmark.append(mark)
                new_method.__dict__["pytestmark"] = new_pytestmark

        if new_method_name in additional_decorators:
            for dec in additional_decorators[new_method_name]:
                new_method = dec(new_method)

        if hasattr(testcase, new_method_name):
            raise RuntimeError(
                f"Tried to autogenerate {new_method_name} but {testcase} already "
                f"has method named {new_method_name}. Please rename the original "
                f"method on the TestCase."
            )
        setattr(testcase, new_method_name, new_method)