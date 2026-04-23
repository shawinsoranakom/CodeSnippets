def instantiate_test(cls, name, test, *, generic_cls=None):
        def instantiate_test_helper(
            cls, name, *, test, param_kwargs=None, decorator_fn=lambda _: []
        ):
            # Add the device param kwarg if the test needs device or devices.
            param_kwargs = {} if param_kwargs is None else param_kwargs
            test_sig_params = inspect.signature(test).parameters
            if "device" in test_sig_params or "devices" in test_sig_params:
                device_arg: str = cls._init_and_get_primary_device()
                if hasattr(test, "num_required_devices"):
                    device_arg = cls.get_all_devices()
                _update_param_kwargs(param_kwargs, "device", device_arg)

            # Apply decorators based on param kwargs.
            for decorator in decorator_fn(param_kwargs):
                test = decorator(test)

            # Constructs the test
            @wraps(test)
            def instantiated_test(self, param_kwargs=param_kwargs):
                # Sets precision and runs test
                # Note: precision is reset after the test is run
                guard_precision = self.precision
                guard_rel_tol = self.rel_tol
                try:
                    self._apply_precision_override_for_test(test, param_kwargs)
                    result = test(self, **param_kwargs)
                except RuntimeError as rte:
                    # check if rte should stop entire test suite.
                    self._stop_test_suite = self._should_stop_test_suite()
                    # Check if test has been decorated with `@expectedFailure`
                    # Using `__unittest_expecting_failure__` attribute, see
                    # https://github.com/python/cpython/blob/ffa505b580464/Lib/unittest/case.py#L164
                    # In that case, make it fail with "unexpected success" by suppressing exception
                    if (
                        getattr(test, "__unittest_expecting_failure__", False)
                        and self._stop_test_suite
                    ):
                        import sys

                        print(
                            "Suppressing fatal exception to trigger unexpected success",
                            file=sys.stderr,
                        )
                        return
                    # raise the runtime error as is for the test suite to record.
                    raise rte
                finally:
                    self.precision = guard_precision
                    self.rel_tol = guard_rel_tol

                return result

            if hasattr(cls, name):
                raise AssertionError(f"Redefinition of test {name}")
            setattr(cls, name, instantiated_test)

        def default_parametrize_fn(test, generic_cls, device_cls):
            # By default, no parametrization is needed.
            yield (test, "", {}, lambda _: [])

        # Parametrization decorators set the parametrize_fn attribute on the test.
        parametrize_fn = getattr(test, "parametrize_fn", default_parametrize_fn)

        # If one of the @dtypes* decorators is present, also parametrize over the dtypes set by it.
        dtypes = cls._get_dtypes(test)
        if dtypes is not None:

            def dtype_parametrize_fn(test, generic_cls, device_cls, dtypes=dtypes):
                for dtype in dtypes:
                    param_kwargs: dict[str, Any] = {}
                    _update_param_kwargs(param_kwargs, "dtype", dtype)

                    # Note that an empty test suffix is set here so that the dtype can be appended
                    # later after the device.
                    yield (test, "", param_kwargs, lambda _: [])

            parametrize_fn = compose_parametrize_fns(
                dtype_parametrize_fn, parametrize_fn
            )

        # Instantiate the parametrized tests.
        for (
            test,  # noqa: B020
            test_suffix,
            param_kwargs,
            decorator_fn,
        ) in parametrize_fn(test, generic_cls, cls):
            test_suffix = "" if test_suffix == "" else "_" + test_suffix
            cls_device_type = (
                cls.device_type
                if cls.device_type != "privateuse1"
                else torch._C._get_privateuse1_backend_name()
            )
            device_suffix = "_" + cls_device_type

            # Note: device and dtype suffix placement
            # Special handling here to place dtype(s) after device according to test name convention.
            dtype_kwarg = None
            if "dtype" in param_kwargs or "dtypes" in param_kwargs:
                dtype_kwarg = (
                    param_kwargs["dtypes"]
                    if "dtypes" in param_kwargs
                    else param_kwargs["dtype"]
                )
            test_name = (
                f"{name}{test_suffix}{device_suffix}{_dtype_test_suffix(dtype_kwarg)}"
            )

            instantiate_test_helper(
                cls=cls,
                name=test_name,
                test=test,
                param_kwargs=param_kwargs,
                decorator_fn=decorator_fn,
            )