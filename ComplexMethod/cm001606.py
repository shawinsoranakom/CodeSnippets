def guess_model_config_from_state_dict(sd, filename):
    sd2_cond_proj_weight = sd.get('cond_stage_model.model.transformer.resblocks.0.attn.in_proj_weight', None)
    diffusion_model_input = sd.get('model.diffusion_model.input_blocks.0.0.weight', None)
    sd2_variations_weight = sd.get('embedder.model.ln_final.weight', None)

    if "model.diffusion_model.x_embedder.proj.weight" in sd:
        return config_sd3

    if sd.get('conditioner.embedders.1.model.ln_final.weight', None) is not None:
        if diffusion_model_input.shape[1] == 9:
            return config_sdxl_inpainting
        else:
            return config_sdxl

    if sd.get('conditioner.embedders.0.model.ln_final.weight', None) is not None:
        return config_sdxl_refiner
    elif sd.get('depth_model.model.pretrained.act_postprocess3.0.project.0.bias', None) is not None:
        return config_depth_model
    elif sd2_variations_weight is not None and sd2_variations_weight.shape[0] == 768:
        return config_unclip
    elif sd2_variations_weight is not None and sd2_variations_weight.shape[0] == 1024:
        return config_unopenclip

    if sd2_cond_proj_weight is not None and sd2_cond_proj_weight.shape[1] == 1024:
        if diffusion_model_input.shape[1] == 9:
            return config_sd2_inpainting
        elif is_using_v_parameterization_for_sd2(sd):
            return config_sd2v
        else:
            return config_sd2

    if diffusion_model_input is not None:
        if diffusion_model_input.shape[1] == 9:
            return config_inpainting
        if diffusion_model_input.shape[1] == 8:
            return config_instruct_pix2pix

    if sd.get('cond_stage_model.roberta.embeddings.word_embeddings.weight', None) is not None:
        if sd.get('cond_stage_model.transformation.weight').size()[0] == 1024:
            return config_alt_diffusion_m18
        return config_alt_diffusion

    return config_default