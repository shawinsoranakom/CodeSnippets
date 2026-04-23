def test_for_nans(x, where):
    if shared.cmd_opts.disable_nan_check:
        return

    if not torch.isnan(x[(0, ) * len(x.shape)]):
        return

    if where == "unet":
        message = "A tensor with NaNs was produced in Unet."

        if not shared.cmd_opts.no_half:
            message += " This could be either because there's not enough precision to represent the picture, or because your video card does not support half type. Try setting the \"Upcast cross attention layer to float32\" option in Settings > Stable Diffusion or using the --no-half commandline argument to fix this."

    elif where == "vae":
        message = "A tensor with NaNs was produced in VAE."

        if not shared.cmd_opts.no_half and not shared.cmd_opts.no_half_vae:
            message += " This could be because there's not enough precision to represent the picture. Try adding --no-half-vae commandline argument to fix this."
    else:
        message = "A tensor with NaNs was produced."

    message += " Use --disable-nan-check commandline argument to disable this check."

    raise NansException(message)