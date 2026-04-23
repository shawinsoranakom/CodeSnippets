def generate_tag_tests(testcase, failures_dict, additional_decorators):
    def generate_test(qualname, definitely_not_pt2_compliant, xfailed_tests):
        def inner(self):
            try:
                op = torch._library.utils.lookup_op(qualname)
            except AttributeError as e:
                # Operator not importable in this test file
                raise unittest.SkipTest(f"Can't import operator {qualname}") from e
            op_marked_as_compliant = torch.Tag.pt2_compliant_tag in op.tags
            if not op_marked_as_compliant:
                return
            if not definitely_not_pt2_compliant:
                return
            raise AssertionError(
                f"op '{qualname}' was tagged with torch.Tag.pt2_compliant_tag "
                f"but it failed some of the generated opcheck tests "
                f"({xfailed_tests}). This may lead to silent correctness issues, "
                f"please fix this."
            )

        return inner

    for qualname, test_dict in failures_dict.data.items():
        xfailed_tests = [
            test
            for test, status_dict in test_dict.items()
            # We're about to delete the following test after Ed's PR
            # to specialize on C++ .size() calls
            if "test_aot_dispatch_static" not in test
            and status_dict["status"] == "xfail"
        ]
        definitely_not_pt2_compliant = len(xfailed_tests) > 0
        generated = generate_test(qualname, definitely_not_pt2_compliant, xfailed_tests)

        # Could result in collisions, but unlikely. We'll raise if we see one below.
        mangled_qualname = qualname.replace("::", "_").replace(".", "_")
        test_name = "test_pt2_compliant_tag_" + mangled_qualname

        # You can skip this test via the additional_decorators argument
        # in generate_opcheck_tests
        if test_name in additional_decorators:
            for decorator in additional_decorators[test_name]:
                generated = decorator(generated)

        if hasattr(testcase, test_name):
            raise RuntimeError(
                f"Tried to generate a test named {test_name}, but it exists "
                f"already. This could be because of a name collision (where "
                f"we generated two tests with the same name), or where we "
                f"generated a test with the same name as an existing test."
            )
        setattr(testcase, test_name, generated)