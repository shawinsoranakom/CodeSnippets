def apply_refiner(cfg_denoiser, sigma=None):
    if opts.refiner_switch_by_sample_steps or sigma is None:
        completed_ratio = cfg_denoiser.step / cfg_denoiser.total_steps
        cfg_denoiser.p.extra_generation_params["Refiner switch by sampling steps"] = True

    else:
        # torch.max(sigma) only to handle rare case where we might have different sigmas in the same batch
        try:
            timestep = torch.argmin(torch.abs(cfg_denoiser.inner_model.sigmas.to(sigma.device) - torch.max(sigma)))
        except AttributeError:  # for samplers that don't use sigmas (DDIM) sigma is actually the timestep
            timestep = torch.max(sigma).to(dtype=int)
        completed_ratio = (999 - timestep) / 1000

    refiner_switch_at = cfg_denoiser.p.refiner_switch_at
    refiner_checkpoint_info = cfg_denoiser.p.refiner_checkpoint_info

    if refiner_switch_at is not None and completed_ratio < refiner_switch_at:
        return False

    if refiner_checkpoint_info is None or shared.sd_model.sd_checkpoint_info == refiner_checkpoint_info:
        return False

    if getattr(cfg_denoiser.p, "enable_hr", False):
        is_second_pass = cfg_denoiser.p.is_hr_pass

        if opts.hires_fix_refiner_pass == "first pass" and is_second_pass:
            return False

        if opts.hires_fix_refiner_pass == "second pass" and not is_second_pass:
            return False

        if opts.hires_fix_refiner_pass != "second pass":
            cfg_denoiser.p.extra_generation_params['Hires refiner'] = opts.hires_fix_refiner_pass

    cfg_denoiser.p.extra_generation_params['Refiner'] = refiner_checkpoint_info.short_title
    cfg_denoiser.p.extra_generation_params['Refiner switch at'] = refiner_switch_at

    with sd_models.SkipWritingToConfig():
        sd_models.reload_model_weights(info=refiner_checkpoint_info)

    devices.torch_gc()
    cfg_denoiser.p.setup_conds()
    cfg_denoiser.update_inner_model()

    return True