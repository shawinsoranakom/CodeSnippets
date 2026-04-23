def get_statistics(local_files_only = False):
    # We log some basic stats about which environment is being used.
    # This is also to check if HuggingFace is down or not!
    # We simply download a README.md file from HF - all data is made public.
    # This is simply so we can check if some envs are broken or not.
    # You can disable this by setting UNSLOTH_DISABLE_STATISTICS
    import os

    if (
        "UNSLOTH_DISABLE_STATISTICS" in os.environ
        or os.environ.get("UNSLOTH_USE_MODELSCOPE", "0") == "1"
    ):
        return
    if local_files_only:
        return
    from huggingface_hub.utils import (
        disable_progress_bars,
        enable_progress_bars,
        are_progress_bars_disabled,
    )

    disabled = False
    if not are_progress_bars_disabled():
        disable_progress_bars()
        disabled = True
    _get_statistics(None)
    _get_statistics("repeat", force_download = False)
    total_memory = (
        torch.xpu.get_device_properties(0).total_memory
        if DEVICE_TYPE == "xpu"
        else torch.cuda.get_device_properties(0).total_memory
    )
    vram = total_memory / 1024 / 1024 / 1024
    if vram <= 8:
        vram = 8
    elif vram <= 16:
        vram = 16
    elif vram <= 20:
        vram = 20
    elif vram <= 24:
        vram = 24
    elif vram <= 40:
        vram = 40
    elif vram <= 48:
        vram = 48
    elif vram <= 80:
        vram = 80
    else:
        vram = 96
    _get_statistics(f"vram-{vram}")
    _get_statistics(f"{DEVICE_COUNT if DEVICE_COUNT <= 8 else 9}")
    if disabled:
        enable_progress_bars()