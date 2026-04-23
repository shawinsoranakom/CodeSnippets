def sample_euler_ancestral_cfg_pp(model, x, sigmas, extra_args=None, callback=None, disable=None, eta=1., s_noise=1., noise_sampler=None):
    """Ancestral sampling with Euler method steps (CFG++)."""
    extra_args = {} if extra_args is None else extra_args
    seed = extra_args.get("seed", None)
    noise_sampler = default_noise_sampler(x, seed=seed) if noise_sampler is None else noise_sampler

    model_sampling = model.inner_model.model_patcher.get_model_object("model_sampling")
    lambda_fn = partial(sigma_to_half_log_snr, model_sampling=model_sampling)

    uncond_denoised = None

    def post_cfg_function(args):
        nonlocal uncond_denoised
        uncond_denoised = args["uncond_denoised"]
        return args["denoised"]

    model_options = extra_args.get("model_options", {}).copy()
    extra_args["model_options"] = comfy.model_patcher.set_model_options_post_cfg_function(model_options, post_cfg_function, disable_cfg1_optimization=True)

    s_in = x.new_ones([x.shape[0]])
    for i in trange(len(sigmas) - 1, disable=disable):
        denoised = model(x, sigmas[i] * s_in, **extra_args)
        if callback is not None:
            callback({'x': x, 'i': i, 'sigma': sigmas[i], 'sigma_hat': sigmas[i], 'denoised': denoised})
        if sigmas[i + 1] == 0:
            # Denoising step
            x = denoised
        else:
            alpha_s = sigmas[i] * lambda_fn(sigmas[i]).exp()
            alpha_t = sigmas[i + 1] * lambda_fn(sigmas[i + 1]).exp()
            d = to_d(x, sigmas[i], alpha_s * uncond_denoised)   # to noise

            # DDIM stochastic sampling
            sigma_down, sigma_up = get_ancestral_step(sigmas[i] / alpha_s, sigmas[i + 1] / alpha_t, eta=eta)
            sigma_down = alpha_t * sigma_down

            # Euler method
            x = alpha_t * denoised + sigma_down * d
            if eta > 0 and s_noise > 0:
                x = x + alpha_t * noise_sampler(sigmas[i], sigmas[i + 1]) * s_noise * sigma_up
    return x