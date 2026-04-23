def _get_fp8_mode_and_check_settings(
    load_in_fp8: Union[bool, str],
    fast_inference: bool,
    full_finetuning: bool = False,
    load_in_4bit: bool = False,
    load_in_8bit: bool = False,
    load_in_16bit: bool = False,
) -> str:
    """
    Assuming `load_in_fp8` is enabled, raise appropriate errors on incompatible settings
    and environment. Currently this feature requires:

    1. H100 GPUs or after
    2. torchao 0.15.0+ (or nightly)
    3. torch 2.9.0+
    4. If fbgemm_gpu_genai is installed, require 1.4.1+

    Returns the fp8 mode, one of "row" or "block".
    """
    assert load_in_fp8 is not False
    if load_in_fp8 is True:
        fp8_mode = "row"  # default
    else:
        fp8_mode = load_in_fp8

    # Check user settings
    if fp8_mode not in ["row", "block"]:
        raise ValueError(
            f"Unsloth: `load_in_fp8` can only be 'row' or 'block', got '{fp8_mode}'"
        )
    if full_finetuning:
        raise ValueError(
            "Unsloth: `load_in_fp8` is not compatible with full finetuning"
        )
    if load_in_4bit or load_in_8bit or load_in_16bit:
        raise ValueError(
            "Unsloth: `load_in_fp8` is not compatible with `load_in_4bit`, `load_in_8bit` or `load_in_16bit`",
        )

    # Check if this is Hopper or above
    if not (
        torch.cuda.is_available()
        and torch.version.cuda
        and torch.cuda.get_device_capability() >= (9, 0)
    ):
        raise ValueError(
            "Unsloth: On the fly `load_in_fp8` requires H100 GPUs or after. Try `unsloth/Qwen3-8B` instead."
        )

    # Check if torch >= 2.9.0
    if Version(torch.__version__) < Version("2.9.0"):
        raise ValueError(
            "Unsloth: On the fly `load_in_fp8` requires torch 2.9.0+. Try `unsloth/Qwen3-8B` instead."
        )

    # Check if torchao has this PR: https://github.com/pytorch/ao/pull/3158,
    # which will be released in 0.15.0.
    if importlib.util.find_spec("torchao") is None:
        raise ValueError(
            "Unsloth: Please install torchao for on the fly float8 to work! Try `unsloth/Qwen3-8B` instead."
        )
    import torchao

    error_message = (
        "Unsloth: `load_in_fp8` requires torchao 0.15.0+ (or nightly).\n"
        f"You have torchao version={torchao.__version__}\n"
        "Use `pip install --upgrade --force-reinstall torchao`"
    )
    if Version(torchao.__version__) < Version("0.15.0"):
        raise ValueError(error_message)

    # If fbgemm_gpu_genai is installed and old, disable FBGEMM and use Triton instead
    if (
        importlib.util.find_spec("fbgemm_gpu") is not None
        and importlib.util.find_spec("fbgemm_gpu.experimental") is not None
    ):
        import fbgemm_gpu.experimental.gen_ai

        if Version(fbgemm_gpu.__version__) < Version("1.4.1"):
            # Old FBGEMM version - disable and use Triton kernels instead
            os.environ["UNSLOTH_HAS_FBGEMM"] = "0"
            from unsloth_zoo.log import logger

            logger.info(
                f"Unsloth: fbgemm_gpu_genai=={fbgemm_gpu.__version__} is old for FP8 loading. "
                f"Using Triton kernels instead."
            )
    return fp8_mode