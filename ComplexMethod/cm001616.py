def samples_to_images_tensor(sample, approximation=None, model=None):
    """Transforms 4-channel latent space images into 3-channel RGB image tensors, with values in range [-1, 1]."""

    if approximation is None or (shared.state.interrupted and opts.live_preview_fast_interrupt):
        approximation = approximation_indexes.get(opts.show_progress_type, 0)

        from modules import lowvram
        if approximation == 0 and lowvram.is_enabled(shared.sd_model) and not shared.opts.live_preview_allow_lowvram_full:
            approximation = 1

    if approximation == 2:
        x_sample = sd_vae_approx.cheap_approximation(sample)
    elif approximation == 1:
        x_sample = sd_vae_approx.model()(sample.to(devices.device, devices.dtype)).detach()
    elif approximation == 3:
        x_sample = sd_vae_taesd.decoder_model()(sample.to(devices.device, devices.dtype)).detach()
        x_sample = x_sample * 2 - 1
    else:
        if model is None:
            model = shared.sd_model
        with torch.no_grad(), devices.without_autocast(): # fixes an issue with unstable VAEs that are flaky even in fp32
            x_sample = model.decode_first_stage(sample.to(model.first_stage_model.dtype))

    return x_sample