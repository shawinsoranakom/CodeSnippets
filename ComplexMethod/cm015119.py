def test_numpy_array_binary_ufunc_promotion(self, device, dtypes):
        import operator
        np_type = torch_to_numpy_dtype_dict[dtypes[0]]
        torch_type = dtypes[1]

        t = torch.tensor((1,), device=device, dtype=torch_type)
        a = np.array((1,), dtype=np_type)
        a_as_t = torch.from_numpy(a).to(device=device)

        for np_first in (True, False):
            for op in (operator.add, torch.add):

                # Acquires results of binary ufunc type promotion.
                try:
                    actual = op(a, t) if np_first else op(t, a)
                except Exception as e:
                    actual = e

                try:
                    expected = op(a_as_t, t) if np_first else op(t, a_as_t)
                except Exception as e:
                    expected = e

                same_result = (type(expected) is type(actual)) and expected == actual

                # Note: An "undesired failure," as opposed to an "expected failure"
                # is both expected (we know the test will fail) and
                # undesirable (if PyTorch was working properly the test would
                # not fail). This test is affected by three issues (see below)
                # that will cause undesired failures. It detects when these
                # issues will occur and updates this bool accordingly.
                undesired_failure = False

                # A NumPy array as the first argument to the plus operator
                # or as any argument to torch.add is not working as
                # intended.
                # See https://github.com/pytorch/pytorch/issues/36363.
                if np_first and op is operator.add:
                    undesired_failure = True
                if op is torch.add:
                    undesired_failure = True

                # Expects the same result if undesired_failure is false
                # and a different result otherwise.
                # Note: These cases prettyprint the failing inputs to make
                # debugging test failures easier.
                if undesired_failure and same_result:
                    msg = (
                        f"Failure: {actual} == {expected}. torch type was {torch_type}. "
                        f"NumPy type was {np_type}. np_first is {np_first} default type is "
                        f"{torch.get_default_dtype()}."
                    )
                    self.fail(msg)

                if not undesired_failure and not same_result:
                    msg = (
                        f"Failure: {actual} != {expected}. torch type was {torch_type}. "
                        f"NumPy type was {np_type}. np_first is {np_first} default type is "
                        f"{torch.get_default_dtype()}."
                    )
                    self.fail(msg)