def mirror_inductor_external_kernels() -> None:
    """
    Copy external kernels into Inductor so they are importable.
    """
    cuda_is_disabled = not str2bool(os.getenv("USE_CUDA"))
    paths = [
        (
            CWD
            / "torch/_inductor/kernel/vendored_templates/cutedsl/kernels/cutedsl_grouped_gemm.py",
            CWD
            / "third_party/cutlass/examples/python/CuTeDSL/blackwell/grouped_gemm.py",
            True,
        ),
    ]
    for new_path, orig_path, allow_missing_if_cuda_is_disabled in paths:
        # Create the dirs involved in new_path if they don't exist
        if not new_path.exists():
            new_path.parent.mkdir(parents=True, exist_ok=True)
            # Add `__init__.py` for find_packages to see `new_path.parent` as a submodule
            (new_path.parent / "__init__.py").touch(exist_ok=True)

        # Copy the files from the orig location to the new location
        if orig_path.is_file():
            shutil.copyfile(orig_path, new_path)
            continue
        if orig_path.is_dir():
            if new_path.exists():
                # copytree fails if the tree exists already, so remove it.
                shutil.rmtree(new_path)
            shutil.copytree(orig_path, new_path)
            continue
        if (
            not orig_path.exists()
            and allow_missing_if_cuda_is_disabled
            and cuda_is_disabled
        ):
            continue
        raise RuntimeError(
            "Check the file paths in `mirror_inductor_external_kernels()`"
        )