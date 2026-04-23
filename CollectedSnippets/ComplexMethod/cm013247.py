def assertExpected(self, s, subname=None):
        r"""
        Test that a string matches the recorded contents of a file
        derived from the name of this test and subname.  This file
        is placed in the 'expect' directory in the same directory
        as the test script. You can automatically update the recorded test
        output using --accept.

        If you call this multiple times in a single function, you must
        give a unique subname each time.
        """
        if not isinstance(s, str):
            raise TypeError("assertExpected is strings only")

        def remove_prefix(text, prefix):
            if text.startswith(prefix):
                return text[len(prefix):]
            return text
        # NB: we take __file__ from the module that defined the test
        # class, so we place the expect directory where the test script
        # lives, NOT where test/common_utils.py lives.  This doesn't matter in
        # PyTorch where all test scripts are in the same directory as
        # test/common_utils.py, but it matters in onnx-pytorch
        module_id = self.__class__.__module__
        munged_id = remove_prefix(self.id(), module_id + ".")
        test_file = os.path.realpath(sys.modules[module_id].__file__)  # type: ignore[type-var]
        expected_file = os.path.join(os.path.dirname(test_file),  # type: ignore[type-var, arg-type]
                                     "expect",
                                     munged_id)

        subname_output = ""
        if subname:
            expected_file += "-" + subname
            subname_output = f" ({subname})"
        expected_file += ".expect"
        expected = None

        def accept_output(update_type):
            print(f"Accepting {update_type} for {munged_id}{subname_output}:\n\n{s}")
            with open(expected_file, 'w') as f:
                # Adjust for producer_version, leave s unmodified
                s_tag = re.sub(r'(producer_version): "[0-9.]*"',
                               r'\1: "CURRENT_VERSION"', s)
                f.write(s_tag)

        try:
            with open(expected_file) as f:
                expected = f.read()
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise
            elif expecttest.ACCEPT:
                return accept_output("output")
            else:
                raise RuntimeError(
                      f"I got this output for {munged_id}{subname_output}:\n\n{s}\n\n"
                      "No expect file exists; to accept the current output, run:\n"
                      f"python {__main__.__file__} {munged_id} --accept") from None

        # a hack for JIT tests
        if IS_WINDOWS:
            expected = re.sub(r'CppOp\[(.+?)\]', 'CppOp[]', expected)
            s = re.sub(r'CppOp\[(.+?)\]', 'CppOp[]', s)

        # Adjust for producer_version
        expected = expected.replace(
            'producer_version: "CURRENT_VERSION"',
            f'producer_version: "{torch.onnx.producer_version}"'
        )
        if expecttest.ACCEPT:
            if expected != s:
                return accept_output("updated output")
        else:
            if hasattr(self, "assertMultiLineEqual"):
                # Python 2.7 only
                # NB: Python considers lhs "old" and rhs "new".
                self.assertMultiLineEqual(expected, s)
            else:
                self.assertEqual(s, expected)