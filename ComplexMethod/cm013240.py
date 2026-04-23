def __init__(self, method_name='runTest', methodName='runTest'):
        # methodName is the correct naming in unittest and testslide uses keyword arguments.
        # So we need to use both to 1) not break BC and, 2) support testslide.
        if methodName != "runTest":
            method_name = methodName
        super().__init__(method_name)

        test_method = getattr(self, method_name, None)
        if test_method is not None:
            # Wraps the tested method if we should do CUDA memory check.
            if TEST_CUDA_MEM_LEAK_CHECK:
                self._do_cuda_memory_leak_check &= getattr(test_method, '_do_cuda_memory_leak_check', True)
                # FIXME: figure out the flaky -1024 anti-leaks on windows. See #8044
                if self._do_cuda_memory_leak_check and not IS_WINDOWS:
                    self.wrap_with_cuda_policy(method_name, self.assertLeaksNoCudaTensors)

            # Wraps the tested method if we should enforce non default CUDA stream.
            self._do_cuda_non_default_stream &= getattr(test_method, '_do_cuda_non_default_stream', True)
            if self._do_cuda_non_default_stream and not IS_WINDOWS:
                self.wrap_with_cuda_policy(method_name, self.enforceNonDefaultStream)

            if self._ignore_not_implemented_error:
                self.wrap_with_policy(method_name, lambda: skip_exception_type(NotImplementedError))

            if PRINT_REPRO_ON_FAILURE:
                try:
                    def _get_rel_test_path(abs_test_path):
                        # Attempt to get relative path based on the "test" dir.
                        # In CI, the working dir is not guaranteed to be the base repo dir so
                        # we can't just compute relative path from that.
                        parts = Path(abs_test_path).parts
                        for i, part in enumerate(parts):
                            if part == "test":
                                base_dir = os.path.join(*parts[:i]) if i > 0 else ''
                                return os.path.relpath(abs_test_path, start=base_dir)

                        # Can't determine containing dir; just return the test filename.
                        # The path isn't strictly correct but it's arguably better than nothing.
                        return os.path.split(abs_test_path)[1]

                    abs_test_path = inspect.getfile(type(self))
                    test_filename = _get_rel_test_path(abs_test_path)
                    class_name = type(self).__name__
                    test_run_cmd = f"python {test_filename} {class_name}.{method_name}"
                    env_var_prefix = TestEnvironment.repro_env_var_prefix()
                    repro_parts = [env_var_prefix, test_run_cmd]
                    self.wrap_with_policy(
                        method_name,
                        lambda repro_parts=repro_parts: print_repro_on_failure(repro_parts))
                except Exception as e:
                    # Don't fail entirely if we can't get the test filename
                    log.info("could not print repro string", extra=str(e))