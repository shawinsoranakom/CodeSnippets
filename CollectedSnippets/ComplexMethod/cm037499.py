def get_vit_attn_backend(
        cls,
        head_size: int,
        dtype: torch.dtype,
        backend: "AttentionBackendEnum | None" = None,
    ) -> "AttentionBackendEnum":
        if backend is not None:
            assert backend in cls.get_supported_vit_attn_backends(), (
                f"Backend {backend} is not supported for vit attention. "
                f"Supported backends are: {cls.get_supported_vit_attn_backends()}"
            )
            logger.info_once(f"Using backend {backend} for vit attention")
            return backend

        from importlib.util import find_spec

        from vllm._aiter_ops import rocm_aiter_ops

        if rocm_aiter_ops.is_enabled() and on_gfx9():
            logger.info_once("Using AITER Flash Attention backend for ViT model.")
            return AttentionBackendEnum.ROCM_AITER_FA

        if (
            on_gfx9()
            and find_spec("flash_attn") is not None
            and (dtype == torch.float16 or dtype == torch.bfloat16)
        ):
            logger.info_once("Using Flash Attention backend for ViT model.")
            return AttentionBackendEnum.FLASH_ATTN

        # RDNA3/RDNA4 (gfx11xx/gfx12xx): Use Flash Attention Triton backend
        if (
            on_gfx1x()
            and flash_attn_triton_available()
            and (dtype == torch.float16 or dtype == torch.bfloat16)
        ):
            logger.info_once(
                "Using Flash Attention (Triton backend) for ViT model on RDNA."
            )
            return AttentionBackendEnum.FLASH_ATTN

        logger.info_once("Using Torch SDPA backend for ViT model.")
        return AttentionBackendEnum.TORCH_SDPA