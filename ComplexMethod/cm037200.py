def _get_attn_isa(
    dtype: torch.dtype, block_size: int, head_size: int | None = None
) -> str:
    if head_size is not None and head_size % 32 != 0 and head_size % 16 == 0:
        return "vec16"
    supports_amx = torch.cpu._is_amx_tile_supported()
    supports_arm = current_platform.get_cpu_architecture() == CpuArchEnum.ARM
    supports_vxe = current_platform.get_cpu_architecture() == CpuArchEnum.S390X
    if supports_amx and dtype in (torch.bfloat16,) and block_size % 32 == 0:
        return "amx"
    elif block_size % 32 == 0:
        if supports_arm:
            # support ARM NEON FMLA and BFMMLA (bf16) for block size 32
            return "neon"
        elif supports_vxe:
            return "vxe"
        else:
            return "vec"
    else:
        return "vec16"