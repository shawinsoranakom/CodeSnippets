def sample_dpmpp_2s_ancestral_RF(model, x, sigmas, extra_args=None, callback=None, disable=None, eta=1., s_noise=1., noise_sampler=None):
    """Ancestral sampling with DPM-Solver++(2S) second-order steps."""
    extra_args = {} if extra_args is None else extra_args
    seed = extra_args.get("seed", None)
    noise_sampler = default_noise_sampler(x, seed=seed) if noise_sampler is None else noise_sampler
    s_in = x.new_ones([x.shape[0]])
    sigma_fn = lambda lbda: (lbda.exp() + 1) ** -1
    lambda_fn = lambda sigma: ((1-sigma)/sigma).log()

    # logged_x = x.unsqueeze(0)

    for i in trange(len(sigmas) - 1, disable=disable):
        denoised = model(x, sigmas[i] * s_in, **extra_args)
        downstep_ratio = 1 + (sigmas[i+1]/sigmas[i] - 1) * eta
        sigma_down = sigmas[i+1] * downstep_ratio
        alpha_ip1 = 1 - sigmas[i+1]
        alpha_down = 1 - sigma_down
        renoise_coeff = (sigmas[i+1]**2 - sigma_down**2*alpha_ip1**2/alpha_down**2)**0.5
        # sigma_down, sigma_up = get_ancestral_step(sigmas[i], sigmas[i + 1], eta=eta)
        if callback is not None:
            callback({'x': x, 'i': i, 'sigma': sigmas[i], 'sigma_hat': sigmas[i], 'denoised': denoised})
        if sigmas[i + 1] == 0:
            # Euler method
            d = to_d(x, sigmas[i], denoised)
            dt = sigma_down - sigmas[i]
            x = x + d * dt
        else:
            # DPM-Solver++(2S)
            if sigmas[i] == 1.0:
                sigma_s = 0.9999
            else:
                t_i, t_down = lambda_fn(sigmas[i]), lambda_fn(sigma_down)
                r = 1 / 2
                h = t_down - t_i
                s = t_i + r * h
                sigma_s = sigma_fn(s)
            # sigma_s = sigmas[i+1]
            sigma_s_i_ratio = sigma_s / sigmas[i]
            u = sigma_s_i_ratio * x + (1 - sigma_s_i_ratio) * denoised
            D_i = model(u, sigma_s * s_in, **extra_args)
            sigma_down_i_ratio = sigma_down / sigmas[i]
            x = sigma_down_i_ratio * x + (1 - sigma_down_i_ratio) * D_i
            # print("sigma_i", sigmas[i], "sigma_ip1", sigmas[i+1],"sigma_down", sigma_down, "sigma_down_i_ratio", sigma_down_i_ratio, "sigma_s_i_ratio", sigma_s_i_ratio, "renoise_coeff", renoise_coeff)
        # Noise addition
        if sigmas[i + 1] > 0 and eta > 0:
            x = (alpha_ip1/alpha_down) * x + noise_sampler(sigmas[i], sigmas[i + 1]) * s_noise * renoise_coeff
        # logged_x = torch.cat((logged_x, x.unsqueeze(0)), dim=0)
    return x