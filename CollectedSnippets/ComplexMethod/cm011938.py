def _aoti_compile_and_package_inner(
    gm: torch.nn.Module,
    # flat_example_inputs: List[Any],
    args: tuple[Any],
    kwargs: dict[str, Any] | None = None,
    *,
    load_and_run: bool = False,
    check_accuracy: str | None = None,
    package_path: str | io.BytesIO | None = None,
    inductor_configs: dict[str, Any] | None = None,
):
    """
    See docstring for aoti_compile_and_package.

    If `load_and_run` is True, this function will load the compiled model and run it.
    This is for the minifier to check the correctness of the compiled model.

    If `check_accuracy` is set, this function will check the accuracy of the compiled
    model against gm. kwargs must be None if check_accuracy is set.
    "strict_accuracy" means "we will minify any time we see anything that
     diverges", whereas "accuracy" is more conservative, and will only minify if there
     is a meaningful fp64 divergence
    """

    if check_accuracy:
        assert kwargs is None or len(kwargs) == 0, (
            "when checking for accuracy, the inputs must have been flattened and kwargs is None"
        )

    from .package import package_aoti

    assert isinstance(gm, torch.fx.GraphModule)

    kwargs = kwargs or {}

    aoti_files = aot_compile(gm, args, kwargs, options=inductor_configs)
    assert isinstance(aoti_files, list)

    if package_path is None:
        path = [
            os.path.splitext(file)[0]
            for file in aoti_files
            if isinstance(file, str) and os.path.splitext(file)[1] == ".so"
        ]
        if len(path) == 0:
            path = [
                os.path.splitext(file)[0]
                for file in aoti_files
                if isinstance(file, str) and os.path.splitext(file)[1] == ".cpp"
            ]
        package_path = path[0] + ".pt2"

    res = package_aoti(package_path, aoti_files)
    assert res == package_path

    if load_and_run or check_accuracy:
        compiled_model = aoti_load_package(package_path)
        if check_accuracy:
            from torch._dynamo.debug_utils import AccuracyError, same_two_models

            # This might look inverted but it's not.  strict_accuracy means "we will
            # minify any time we see anything that diverges", whereas accuracy is more
            # conservative, and will only minify if there is a meaningful fp64
            # divergence
            not_strict_accuracy = check_accuracy == "accuracy"
            if not same_two_models(
                gm,
                compiled_model,  # type: ignore[arg-type]
                args,
                only_fwd=True,
                require_fp64=not_strict_accuracy,
                ignore_non_fp=not_strict_accuracy,
            ):
                raise AccuracyError("Bad accuracy detected")
        else:
            compiled_model(*args, **kwargs)

    return package_path