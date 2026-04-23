def sample_dpmpp_sde(model, x, sigmas, extra_args=None, callback=None, disable=None, eta=1., s_noise=1., noise_sampler=None, r=1 / 2):
    """DPM-Solver++ (stochastic)."""
    if len(sigmas) <= 1:
        return x

    extra_args = {} if extra_args is None else extra_args
    sigma_min, sigma_max = sigmas[sigmas > 0].min(), sigmas.max()
    seed = extra_args.get("seed", None)
    noise_sampler = BrownianTreeNoiseSampler(x, sigma_min, sigma_max, seed=seed, cpu=True) if noise_sampler is None else noise_sampler
    s_in = x.new_ones([x.shape[0]])

    model_sampling = model.inner_model.model_patcher.get_model_object('model_sampling')
    sigma_fn = partial(half_log_snr_to_sigma, model_sampling=model_sampling)
    lambda_fn = partial(sigma_to_half_log_snr, model_sampling=model_sampling)
    sigmas = offset_first_sigma_for_snr(sigmas, model_sampling)

    for i in trange(len(sigmas) - 1, disable=disable):
        denoised = model(x, sigmas[i] * s_in, **extra_args)
        if callback is not None:
            callback({'x': x, 'i': i, 'sigma': sigmas[i], 'sigma_hat': sigmas[i], 'denoised': denoised})
        if sigmas[i + 1] == 0:
            # Denoising step
            x = denoised
        else:
            # DPM-Solver++
            lambda_s, lambda_t = lambda_fn(sigmas[i]), lambda_fn(sigmas[i + 1])
            h = lambda_t - lambda_s
            lambda_s_1 = lambda_s + r * h
            fac = 1 / (2 * r)

            sigma_s_1 = sigma_fn(lambda_s_1)

            alpha_s = sigmas[i] * lambda_s.exp()
            alpha_s_1 = sigma_s_1 * lambda_s_1.exp()
            alpha_t = sigmas[i + 1] * lambda_t.exp()

            # Step 1
            sd, su = get_ancestral_step(lambda_s.neg().exp(), lambda_s_1.neg().exp(), eta)
            lambda_s_1_ = sd.log().neg()
            h_ = lambda_s_1_ - lambda_s
            x_2 = (alpha_s_1 / alpha_s) * (-h_).exp() * x - alpha_s_1 * (-h_).expm1() * denoised
            if eta > 0 and s_noise > 0:
                x_2 = x_2 + alpha_s_1 * noise_sampler(sigmas[i], sigma_s_1) * s_noise * su
            denoised_2 = model(x_2, sigma_s_1 * s_in, **extra_args)

            # Step 2
            sd, su = get_ancestral_step(lambda_s.neg().exp(), lambda_t.neg().exp(), eta)
            lambda_t_ = sd.log().neg()
            h_ = lambda_t_ - lambda_s
            denoised_d = (1 - fac) * denoised + fac * denoised_2
            x = (alpha_t / alpha_s) * (-h_).exp() * x - alpha_t * (-h_).expm1() * denoised_d
            if eta > 0 and s_noise > 0:
                x = x + alpha_t * noise_sampler(sigmas[i], sigmas[i + 1]) * s_noise * su
    return x