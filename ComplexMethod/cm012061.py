def get_rocm_target_archs() -> list[str]:
    env_archs = os.environ.get("PYTORCH_ROCM_ARCH", "").strip()
    if env_archs:
        archs = [arch.strip() for arch in env_archs.replace(";", ",").split(",")]
        archs = [arch for arch in archs if arch]
        if archs:
            # Ensure current device arch is included
            if torch.cuda.is_available():
                for dev_idx in range(torch.cuda.device_count()):
                    current_arch = torch.cuda.get_device_properties(
                        dev_idx
                    ).gcnArchName.split(":")[0]
                    if current_arch not in archs:
                        archs.append(current_arch)
            return archs

    try:
        from torch._inductor import config

        if hasattr(config, "rocm") and hasattr(config.rocm, "target_archs"):
            archs = config.rocm.target_archs
            if archs:
                return archs

    except Exception:
        pass

    return torch.cuda.get_arch_list()