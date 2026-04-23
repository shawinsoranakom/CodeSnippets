def sample_gradient_estimation(model, x, sigmas, extra_args=None, callback=None, disable=None, ge_gamma=2., cfg_pp=False):
    """Gradient-estimation sampler. Paper: https://openreview.net/pdf?id=o2ND9v0CeK"""
    extra_args = {} if extra_args is None else extra_args
    s_in = x.new_ones([x.shape[0]])
    old_d = None

    uncond_denoised = None
    def post_cfg_function(args):
        nonlocal uncond_denoised
        uncond_denoised = args["uncond_denoised"]
        return args["denoised"]

    if cfg_pp:
        model_options = extra_args.get("model_options", {}).copy()
        extra_args["model_options"] = comfy.model_patcher.set_model_options_post_cfg_function(model_options, post_cfg_function, disable_cfg1_optimization=True)

    for i in trange(len(sigmas) - 1, disable=disable):
        denoised = model(x, sigmas[i] * s_in, **extra_args)
        if cfg_pp:
            d = to_d(x, sigmas[i], uncond_denoised)
        else:
            d = to_d(x, sigmas[i], denoised)
        if callback is not None:
            callback({'x': x, 'i': i, 'sigma': sigmas[i], 'sigma_hat': sigmas[i], 'denoised': denoised})
        dt = sigmas[i + 1] - sigmas[i]
        if sigmas[i + 1] == 0:
            # Denoising step
            x = denoised
        else:
            # Euler method
            if cfg_pp:
                x = denoised + d * sigmas[i + 1]
            else:
                x = x + d * dt

            if i >= 1:
                # Gradient estimation
                d_bar = (ge_gamma - 1) * (d - old_d)
                x = x + d_bar * dt
        old_d = d
    return x