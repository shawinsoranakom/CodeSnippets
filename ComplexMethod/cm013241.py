def _run_custom(self, result=None):
        using_unittest = isinstance(result, unittest.TestResult)

        super_run = super().run
        test_cls = super_run.__self__  # type: ignore[attr-defined]

        # Are we compiling?
        compiled = TEST_WITH_TORCHDYNAMO or TEST_WITH_AOT_EAGER or TEST_WITH_TORCHINDUCTOR
        # Is the class strict and compiling?
        strict_default = False
        should_reset_dynamo = False

        # We disable size_asserts for test_ops since some tests fail
        # due to mismatch of strides returned from eager v.s. meta kernels
        # Only some of the ops has this problem, but since tests in
        # test_op.py are parametrized, it's hard to do this specifically
        # for the affected ops.
        # It's not a big deal since these problems are captured by
        # test_torchinductor_opinfo.py as well.
        should_disable_size_asserts = False
        if compiled:
            try:
                path = inspect.getfile(type(test_cls))
                full_path = os.path.abspath(path)
                match = re.match(r".*/test/(.*).py", full_path)
                if match is not None:
                    filename = match.group(1)
                    if TEST_WITH_TORCHINDUCTOR:
                        from .dynamo_test_failures import FIXME_inductor_non_strict
                        strict_default = filename not in FIXME_inductor_non_strict
                        should_reset_dynamo = True

                        if filename == "test_ops":
                            should_disable_size_asserts = True
                    else:
                        strict_default = True
            # inspect.getfile can fail with these
            except (OSError, TypeError):
                pass
            if "STRICT_DEFAULT" in os.environ:
                if os.environ["STRICT_DEFAULT"] == "1":
                    strict_default = True

        strict_mode = False
        if compiled:
            test_method = getattr(self, self._testMethodName)
            if hasattr(test_method, "dynamo_strict"):
                strict_mode = test_method.dynamo_strict
            elif hasattr(test_cls, "dynamo_strict"):
                strict_mode = test_cls.dynamo_strict
            else:
                strict_mode = strict_default
        nopython = getattr(test_cls, "dynamo_strict_nopython", False) and compiled

        if strict_mode or should_reset_dynamo:
            torch._dynamo.reset()

        torch.compiler.set_stance("default")

        # TODO: Remove this; this is grandfathered in because we suppressed errors
        # on test suite previously
        # When strict mode is False, suppress_errors is True
        if compiled:
            suppress_errors = not strict_mode
        else:
            suppress_errors = torch._dynamo.config.suppress_errors

        maybe_disable_size_asserts = (
            torch._inductor.config.patch(size_asserts=False)
            if should_disable_size_asserts
            else contextlib.nullcontext()
        )

        with unittest.mock.patch("torch._dynamo.config.suppress_errors", suppress_errors), maybe_disable_size_asserts:
            if TEST_WITH_AOT_EAGER:
                super_run = self.compile_fn(super_run, "aot_eager_decomp_partition", nopython)
            elif TEST_WITH_TORCHDYNAMO or TEST_WITH_TORCHINDUCTOR:
                if TEST_WITH_TORCHINDUCTOR:
                    super_run = self.compile_fn(super_run, "inductor", nopython)
                else:
                    # Assume eager-generated GraphModules will not error out.
                    # If we do, this is probably a Dynamo bug!
                    super_run = self.compile_fn(super_run, "eager_noexcept", nopython)

                key = self._dynamo_test_key()

                def expect_failure(f, file_name):
                    @wraps(f)
                    def wrapper(*args, **kwargs):
                        try:
                            f(*args, **kwargs)
                        except BaseException as e:
                            self.skipTest(e)
                        raise RuntimeError(f"Unexpected success, please remove `{file_name}`")
                    return wrapper

                if TEST_WITH_TORCHINDUCTOR:
                    subdir = "test/inductor_expected_failures"
                    from .dynamo_test_failures import inductor_expected_failures as expected_failures
                else:
                    subdir = "test/dynamo_expected_failures"
                    from .dynamo_test_failures import dynamo_expected_failures as expected_failures

                if key in expected_failures:
                    method = getattr(self, self._testMethodName)
                    file_name = os.path.join(subdir, key)
                    setattr(self, self._testMethodName, expect_failure(method, file_name))

                def ignore_failure(f, file_name):
                    @wraps(f)
                    def wrapper(*args, **kwargs):
                        try:
                            f(*args, **kwargs)
                        except BaseException as e:
                            self.skipTest(e)
                        method = getattr(self, self._testMethodName)
                        if getattr(method, "__unittest_expecting_failure__", False):
                            self.skipTest("unexpected success")
                        else:
                            self.skipTest(f"This test passed, maybe we can remove `{file_name}`")
                    return wrapper

                if TEST_WITH_TORCHINDUCTOR:
                    subdir = "test/inductor_skips"
                    from .dynamo_test_failures import inductor_skips as skips
                else:
                    subdir = "test/dynamo_skips"
                    from .dynamo_test_failures import dynamo_skips as skips

                if key in skips:
                    method = getattr(self, self._testMethodName)
                    file_name = os.path.join(subdir, key)
                    setattr(self, self._testMethodName, ignore_failure(method, file_name))

                from .dynamo_test_failures import compiled_autograd_skips
                if torch._dynamo.config.compiled_autograd and key in compiled_autograd_skips:
                    # Still run the test, but with compiled autograd disabled
                    super_run = runWithoutCompiledAutograd()(super_run)

            super_run(result=result)

        if strict_mode or should_reset_dynamo:
            torch._dynamo.reset()
        elif torch._dynamo.config.compiled_autograd:
            torch._dynamo.compiled_autograd.reset()

        # Early terminate test if necessary.  If using pytest, use the -x flag instead
        if using_unittest and self._should_stop_test_suite():
            if result.wasSuccessful():
                case = TestCase()
                if TEST_SAVE_XML is not None:
                    # This is a big hacky, XMLRunner modifies expected type from TestCase to TestInfo
                    # Create dummy TestInfo to record results correctly
                    from xmlrunner.result import _TestInfo  # type: ignore[import]
                    case = _TestInfo(result, case)
                    case.output = _TestInfo.ERROR  # type: ignore[attr-defined]
                    case.elapsed_time = 0.0  # type: ignore[attr-defined]
                    case.test_description = "TestSuiteEarlyFailure"  # type: ignore[attr-defined]
                # This shouldn't really happen, but if does add fake failure
                # For more details see https://github.com/pytorch/pytorch/issues/71973
                result.failures.append((case, "TestSuite execution was aborted early"))
                if result.wasSuccessful() is not False:
                    raise AssertionError("expected result.wasSuccessful() to be False after adding failure")
            result.stop()