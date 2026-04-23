def res_multistep(model, x, sigmas, extra_args=None, callback=None, disable=None, s_noise=1., noise_sampler=None, eta=1., cfg_pp=False):
    extra_args = {} if extra_args is None else extra_args
    seed = extra_args.get("seed", None)
    noise_sampler = default_noise_sampler(x, seed=seed) if noise_sampler is None else noise_sampler
    s_in = x.new_ones([x.shape[0]])
    sigma_fn = lambda t: t.neg().exp()
    t_fn = lambda sigma: sigma.log().neg()
    phi1_fn = lambda t: torch.expm1(t) / t
    phi2_fn = lambda t: (phi1_fn(t) - 1.0) / t

    old_sigma_down = None
    old_denoised = None
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
        sigma_down, sigma_up = get_ancestral_step(sigmas[i], sigmas[i + 1], eta=eta)
        if callback is not None:
            callback({"x": x, "i": i, "sigma": sigmas[i], "sigma_hat": sigmas[i], "denoised": denoised})
        if sigma_down == 0 or old_denoised is None:
            # Euler method
            if cfg_pp:
                d = to_d(x, sigmas[i], uncond_denoised)
                x = denoised + d * sigma_down
            else:
                d = to_d(x, sigmas[i], denoised)
                dt = sigma_down - sigmas[i]
                x = x + d * dt
        else:
            # Second order multistep method in https://arxiv.org/pdf/2308.02157
            t, t_old, t_next, t_prev = t_fn(sigmas[i]), t_fn(old_sigma_down), t_fn(sigma_down), t_fn(sigmas[i - 1])
            h = t_next - t
            c2 = (t_prev - t_old) / h

            phi1_val, phi2_val = phi1_fn(-h), phi2_fn(-h)
            b1 = torch.nan_to_num(phi1_val - phi2_val / c2, nan=0.0)
            b2 = torch.nan_to_num(phi2_val / c2, nan=0.0)

            if cfg_pp:
                x = x + (denoised - uncond_denoised)
                x = sigma_fn(h) * x + h * (b1 * uncond_denoised + b2 * old_denoised)
            else:
                x = sigma_fn(h) * x + h * (b1 * denoised + b2 * old_denoised)

        # Noise addition
        if sigmas[i + 1] > 0:
            x = x + noise_sampler(sigmas[i], sigmas[i + 1]) * s_noise * sigma_up

        if cfg_pp:
            old_denoised = uncond_denoised
        else:
            old_denoised = denoised
        old_sigma_down = sigma_down
    return x