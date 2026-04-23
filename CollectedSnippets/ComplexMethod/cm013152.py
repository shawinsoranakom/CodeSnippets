def _parametrize_test(self, test, generic_cls, device_cls):
        """Parameterizes the given test function across each op and its associated dtypes."""
        if device_cls is None:
            raise RuntimeError(
                "The @ops decorator is only intended to be used in a device-specific "
                "context; use it with instantiate_device_type_tests() instead of "
                "instantiate_parametrized_tests()"
            )

        op = check_exhausted_iterator = object()
        for op in self.op_list:
            # Determine the set of dtypes to use.
            dtypes: set[torch.dtype] | set[None]
            if isinstance(self.opinfo_dtypes, Sequence):
                dtypes = set(self.opinfo_dtypes)
            elif self.opinfo_dtypes == OpDTypes.unsupported_backward:
                dtypes = set(get_all_dtypes()).difference(
                    op.supported_backward_dtypes(device_cls.device_type)
                )
            elif self.opinfo_dtypes == OpDTypes.supported_backward:
                dtypes = op.supported_backward_dtypes(device_cls.device_type)
            elif self.opinfo_dtypes == OpDTypes.unsupported:
                dtypes = set(get_all_dtypes()).difference(
                    op.supported_dtypes(device_cls.device_type)
                )
            elif self.opinfo_dtypes == OpDTypes.supported:
                dtypes = set(op.supported_dtypes(device_cls.device_type))
            elif self.opinfo_dtypes == OpDTypes.any_one:
                # Tries to pick a dtype that supports both forward or backward
                supported = set(op.supported_dtypes(device_cls.device_type))
                supported_backward = op.supported_backward_dtypes(
                    device_cls.device_type
                )
                supported_both = supported.intersection(supported_backward)
                dtype_set = supported_both if len(supported_both) > 0 else supported
                for dtype in ANY_DTYPE_ORDER:
                    if dtype in dtype_set:
                        dtypes = {dtype}
                        break
                else:
                    dtypes = {}
            elif self.opinfo_dtypes == OpDTypes.any_common_cpu_cuda_one:
                # Tries to pick a dtype that supports both CPU and CUDA
                supported = set(op.dtypes).intersection(op.dtypesIfCUDA)
                if supported:
                    dtypes = {
                        next(dtype for dtype in ANY_DTYPE_ORDER if dtype in supported)
                    }
                else:
                    dtypes = {}

            elif self.opinfo_dtypes == OpDTypes.none:
                dtypes = {None}
            else:
                raise RuntimeError(f"Unknown OpDType: {self.opinfo_dtypes}")

            if self.allowed_dtypes is not None:
                dtypes = dtypes.intersection(self.allowed_dtypes)

            # Construct the test name; device / dtype parts are handled outside.
            # See [Note: device and dtype suffix placement]
            test_name = op.formatted_name

            # Filter sample skips / xfails to only those that apply to the OpInfo.
            # These are defined on the test function via decorators.
            sample_skips_and_xfails = getattr(test, "sample_skips_and_xfails", None)
            if sample_skips_and_xfails is not None:
                sample_skips_and_xfails = [
                    rule
                    for rule in sample_skips_and_xfails
                    if rule.op_match_fn(device_cls.device_type, op)
                ]

            for dtype in dtypes:
                # Construct parameter kwargs to pass to the test.
                param_kwargs = {"op": op}
                _update_param_kwargs(param_kwargs, "dtype", dtype)

                # NOTE: test_wrapper exists because we don't want to apply
                #   op-specific decorators to the original test.
                #   Test-specific decorators are applied to the original test,
                #   however.
                try:

                    @wraps(test)
                    def test_wrapper(*args, **kwargs):
                        try:
                            return test(*args, **kwargs)
                        except unittest.SkipTest as e:
                            raise e
                        except Exception as e:
                            tracked_input = get_tracked_input()
                            if PRINT_REPRO_ON_FAILURE and tracked_input is not None:
                                e_tracked = Exception(
                                    f"{str(e)}\n\nCaused by {tracked_input.type_desc} "
                                    f"at index {tracked_input.index}: "
                                    f"{_serialize_sample(tracked_input.val)}"
                                )
                                e_tracked._tracked_input = tracked_input  # type: ignore[attr]
                                raise e_tracked from e
                            raise e
                        finally:
                            clear_tracked_input()

                    if self.skip_if_dynamo and not TEST_WITH_TORCHINDUCTOR:
                        test_wrapper = skipIfTorchDynamo(
                            "Policy: we don't run OpInfo tests w/ Dynamo"
                        )(test_wrapper)

                    # Initialize info for the last input seen. This is useful for tracking
                    # down which inputs caused a test failure. Note that TrackedInputIter is
                    # responsible for managing this.
                    test.tracked_input = None

                    decorator_fn = partial(
                        op.get_decorators,
                        generic_cls.__name__,
                        test.__name__,
                        device_cls.device_type,
                        dtype,
                    )

                    if sample_skips_and_xfails is not None:
                        test_wrapper.sample_skips_and_xfails = sample_skips_and_xfails

                    yield (test_wrapper, test_name, param_kwargs, decorator_fn)
                except Exception as ex:
                    # Provides an error message for debugging before rethrowing the exception
                    print(f"Failed to instantiate {test_name} for op {op.name}!")
                    raise ex
        if op is check_exhausted_iterator:
            raise ValueError(
                "An empty op_list was passed to @ops. "
                "Note that this may result from reuse of a generator."
            )