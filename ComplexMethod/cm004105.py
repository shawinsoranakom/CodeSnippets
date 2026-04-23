def adapt_internal_ckpt(ov_sd):
    # Replace values instead of keys, and remove any isinstance checks
    sam2_sd = {k: v.replace("backbone.vision_backbone.trunk", "image_encoder.trunk") for k, v in ov_sd.items()}
    sam2_sd = {k: v.replace("backbone.vision_backbone.convs", "image_encoder.neck.convs") for k, v in sam2_sd.items()}
    # rename components to be consitent with paper and public release
    sam2_sd = {k: v.replace("transformer.encoder", "memory_attention") for k, v in sam2_sd.items()}
    sam2_sd = {k: v.replace("maskmem_backbone", "memory_encoder") for k, v in sam2_sd.items()}
    sam2_sd = {
        k: v.replace(
            "memory_encoder.mask_downsampler.encoder.0.",
            "memory_encoder.mask_downsampler.layers.0.conv.",
        )
        for k, v in sam2_sd.items()
    }
    sam2_sd = {
        k: v.replace(
            "memory_encoder.mask_downsampler.encoder.1.",
            "memory_encoder.mask_downsampler.layers.0.layer_norm.",
        )
        for k, v in sam2_sd.items()
    }
    sam2_sd = {
        k: v.replace(
            "memory_encoder.mask_downsampler.encoder.3.",
            "memory_encoder.mask_downsampler.layers.1.conv.",
        )
        for k, v in sam2_sd.items()
    }
    sam2_sd = {
        k: v.replace(
            "memory_encoder.mask_downsampler.encoder.4.",
            "memory_encoder.mask_downsampler.layers.1.layer_norm.",
        )
        for k, v in sam2_sd.items()
    }
    sam2_sd = {
        k: v.replace(
            "memory_encoder.mask_downsampler.encoder.6.",
            "memory_encoder.mask_downsampler.layers.2.conv.",
        )
        for k, v in sam2_sd.items()
    }
    sam2_sd = {
        k: v.replace(
            "memory_encoder.mask_downsampler.encoder.7.",
            "memory_encoder.mask_downsampler.layers.2.layer_norm.",
        )
        for k, v in sam2_sd.items()
    }
    sam2_sd = {
        k: v.replace(
            "memory_encoder.mask_downsampler.encoder.9.",
            "memory_encoder.mask_downsampler.layers.3.conv.",
        )
        for k, v in sam2_sd.items()
    }
    sam2_sd = {
        k: v.replace(
            "memory_encoder.mask_downsampler.encoder.10.",
            "memory_encoder.mask_downsampler.layers.3.layer_norm.",
        )
        for k, v in sam2_sd.items()
    }
    sam2_sd = {
        k: v.replace(
            "memory_encoder.mask_downsampler.encoder.12.",
            "memory_encoder.mask_downsampler.final_conv.",
        )
        for k, v in sam2_sd.items()
    }
    sam2_sd = {
        k: v.replace(
            "memory_encoder.o_proj.",
            "memory_encoder.projection.",
        )
        for k, v in sam2_sd.items()
    }
    # MLPBLock to MLP
    sam2_sd = {
        k: v.replace("mask_decoder.transformer.layers.0.mlp.lin1", "mask_decoder.transformer.layers.0.mlp.layers.0")
        for k, v in sam2_sd.items()
    }
    sam2_sd = {
        k: v.replace("mask_decoder.transformer.layers.0.mlp.lin2", "mask_decoder.transformer.layers.0.mlp.layers.1")
        for k, v in sam2_sd.items()
    }
    sam2_sd = {
        k: v.replace("mask_decoder.transformer.layers.1.mlp.lin1", "mask_decoder.transformer.layers.1.mlp.layers.0")
        for k, v in sam2_sd.items()
    }
    sam2_sd = {
        k: v.replace("mask_decoder.transformer.layers.1.mlp.lin2", "mask_decoder.transformer.layers.1.mlp.layers.1")
        for k, v in sam2_sd.items()
    }
    sam2_sd = {
        k: v.replace(
            "mask_decoder.transformer.layers.0.mlp.layers.0.",
            "mask_decoder.transformer.layers.0.mlp.proj_in.",
        )
        for k, v in sam2_sd.items()
    }
    sam2_sd = {
        k: v.replace(
            "mask_decoder.transformer.layers.0.mlp.layers.1.",
            "mask_decoder.transformer.layers.0.mlp.proj_out.",
        )
        for k, v in sam2_sd.items()
    }
    sam2_sd = {
        k: v.replace(
            "mask_decoder.transformer.layers.1.mlp.layers.0.",
            "mask_decoder.transformer.layers.1.mlp.proj_in.",
        )
        for k, v in sam2_sd.items()
    }
    sam2_sd = {
        k: v.replace(
            "mask_decoder.transformer.layers.1.mlp.layers.1.",
            "mask_decoder.transformer.layers.1.mlp.proj_out.",
        )
        for k, v in sam2_sd.items()
    }
    # FFN to MLP
    # sam2_sd = {k: v.replace(".fc1", ".layers.0") for k, v in sam2_sd.items()}
    # sam2_sd = {k: v.replace(".fc2", ".layers.1") for k, v in sam2_sd.items()}
    return sam2_sd