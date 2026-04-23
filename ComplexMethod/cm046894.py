def fix_vllm_pdl_blackwell():
    """
    Fix vLLM PDL (Programmatic Dependent Launch) bug on Blackwell GPUs (SM100).

    The issue: vLLM's LoRA Triton kernels use tl.extra.cuda.gdc_wait() for PDL
    optimization on SM90+ GPUs. This fails on SM100 (B200/B100) during CUDA graph
    capture because Triton's pipeliner can't handle gdc_wait in complex kernels.

    See: https://github.com/vllm-project/vllm/issues/30872
    """
    if importlib.util.find_spec("vllm") is None:
        return

    # Check if any CUDA GPU is SM100 (Blackwell)
    try:
        import torch

        if not torch.cuda.is_available():
            return

        # Scan all GPUs for SM100 - fix applies globally via env var and monkey-patch
        has_sm100 = False
        sm100_gpu_name = None
        for i in range(torch.cuda.device_count()):
            major, minor = torch.cuda.get_device_capability(i)
            if major == 10:
                has_sm100 = True
                sm100_gpu_name = torch.cuda.get_device_name(i)
                break

        if not has_sm100:
            return
    except Exception:
        return

    # Helper to check if module spec exists
    def _spec_exists(name):
        try:
            return importlib.util.find_spec(name) is not None
        except (ImportError, OSError, ModuleNotFoundError, ValueError):
            return False

    # Check if vLLM has the PDL-related modules before doing internet check
    has_utils = _spec_exists("vllm.lora.ops.triton_ops.utils")
    has_expand_op = _spec_exists("vllm.lora.ops.triton_ops.lora_expand_op")
    has_shrink_op = _spec_exists("vllm.lora.ops.triton_ops.lora_shrink_op")

    if not has_utils and not has_expand_op and not has_shrink_op:
        # Old vLLM version without PDL support - nothing to patch
        return

    # Check if vLLM version includes the fix
    VLLM_PDL_FIX_VERSION = "0.15.0"
    try:
        vllm_version = Version(importlib_version("vllm"))
        if vllm_version >= Version(VLLM_PDL_FIX_VERSION):
            logger.info(
                f"Unsloth: SM100 ({sm100_gpu_name}) detected but vLLM {vllm_version} "
                f"should include PDL fix - skipping workaround"
            )
            return
    except Exception as e:
        logger.debug(
            f"Unsloth: vLLM version check failed ({e}), applying PDL workaround."
        )

    # Apply the PDL fix
    os.environ["TRITON_DISABLE_PDL"] = "1"

    def fake_supports_pdl(*args, **kwargs):
        return False

    patched = []
    patched_names = set()

    def _record_patch(name):
        if name not in patched_names:
            patched.append(name)
            patched_names.add(name)

    # First, patch the source module (utils.py) where supports_pdl is defined.
    # This is critical because supports_pdl uses @lru_cache - we must clear the
    # cache to prevent stale cached results from the original function.
    try:
        utils_module = importlib.import_module("vllm.lora.ops.triton_ops.utils")
        if hasattr(utils_module, "supports_pdl"):
            original_fn = utils_module.supports_pdl
            if hasattr(original_fn, "cache_clear"):
                original_fn.cache_clear()
            utils_module.supports_pdl = fake_supports_pdl
            _record_patch("utils")
    except (ImportError, ModuleNotFoundError, AttributeError):
        pass

    # Also patch the consumer modules that import supports_pdl from utils.
    # This ensures the patched function is used even if the module was already
    # imported before this fix runs.
    consumer_modules = {
        "lora_expand_op": "vllm.lora.ops.triton_ops.lora_expand_op",
        "lora_shrink_op": "vllm.lora.ops.triton_ops.lora_shrink_op",
        "fused_moe_lora_op": "vllm.lora.ops.triton_ops.fused_moe_lora_op",
    }
    for name, path in consumer_modules.items():
        try:
            module = importlib.import_module(path)
            if hasattr(module, "supports_pdl"):
                module.supports_pdl = fake_supports_pdl
                _record_patch(name)
        except (ImportError, ModuleNotFoundError, AttributeError):
            pass

    # Patch any additional already-loaded triton ops consumers that expose supports_pdl.
    for module_name, module in tuple(sys.modules.items()):
        if not module_name.startswith("vllm.lora.ops.triton_ops."):
            continue
        if module is None or not hasattr(module, "supports_pdl"):
            continue
        module.supports_pdl = fake_supports_pdl
        _record_patch(module_name.rsplit(".", 1)[-1])

    if patched:
        logger.info(
            f"Unsloth: Applied PDL fix for SM100 ({sm100_gpu_name}) - "
            f"patched: {', '.join(patched)}"
        )
    else:
        # Just set the env var - vLLM might be an older version without supports_pdl
        logger.info(f"Unsloth: Set TRITON_DISABLE_PDL=1 for SM100 ({sm100_gpu_name})")