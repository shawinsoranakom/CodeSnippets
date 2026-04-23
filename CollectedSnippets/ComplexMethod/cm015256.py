def run_with_nativert(ep):
    # Downstream tests might mutate the exported program in subtle ways, so
    # we need to make a copy here.
    ep_infer = copy.deepcopy(ep)
    ep_infer = _use_real_inputs(ep_infer.run_decompositions())
    MODEL_NAME = "forward"

    # TODO Does named tempfile have collision?
    with tempfile.NamedTemporaryFile(suffix=".pt2") as f:
        torch.export.pt2_archive._package.package_pt2(
            f, exported_programs={MODEL_NAME: ep_infer}
        )
        filename = f.name

        try:
            ep_args, ep_kwargs = ep_infer.example_inputs
            ep_args_copied, ep_kwargs_copied = (
                copy.deepcopy(ep_args),
                copy.deepcopy(ep_kwargs),
            )
            torch.manual_seed(0)
            try:
                flat_expected = pytree.tree_leaves(
                    ep_infer.module()(*ep_args_copied, **ep_kwargs_copied)
                )
            except Exception as e:
                raise unittest.case.SkipTest(str(e)) from e

            model_runner = PyModelRunner(filename, MODEL_NAME)
            torch.manual_seed(0)
            if _is_supported_types((ep_args, ep_kwargs)):
                results = model_runner.run(*ep_args, **ep_kwargs)
            else:
                results = model_runner.run_with_flat_inputs_and_outputs(
                    *pytree.tree_leaves((ep_args, ep_kwargs))
                )
            flat_results = pytree.tree_leaves(results)
            if len(flat_results) != len(flat_expected):
                raise AssertionError(
                    f"Expected {len(flat_expected)} results, got {len(flat_results)}"
                )
            for result, expected in zip(flat_results, flat_expected):
                if type(result) is not type(expected):
                    raise AssertionError(
                        f"Expected type {type(expected)}, got {type(result)}"
                    )
                if isinstance(result, torch.Tensor) and isinstance(
                    expected, torch.Tensor
                ):
                    if result.shape != expected.shape:
                        raise AssertionError(
                            f"Expected shape {expected.shape}, got {result.shape}"
                        )
                    if result.dtype != expected.dtype:
                        raise AssertionError(
                            f"Expected dtype {expected.dtype}, got {result.dtype}"
                        )
                    if result.device != expected.device:
                        raise AssertionError(
                            f"Expected device {expected.device}, got {result.device}"
                        )
                    torch.testing.assert_close(result, expected, equal_nan=True)
                else:
                    if result != expected:
                        raise AssertionError(f"Expected {expected}, got {result}")
        except RuntimeError as e:
            # User need to register pytree type on the cpp side, which
            # cannot be tested in python unittest.
            if "Unknown pytree node type" in str(e):
                pass
            else:
                raise e
        return ep