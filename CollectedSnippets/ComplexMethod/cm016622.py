def sample_sa_solver(model, x, sigmas, extra_args=None, callback=None, disable=False, tau_func=None, s_noise=1.0, noise_sampler=None, predictor_order=3, corrector_order=4, use_pece=False, simple_order_2=False):
    """Stochastic Adams Solver with predictor-corrector method (NeurIPS 2023)."""
    if len(sigmas) <= 1:
        return x
    extra_args = {} if extra_args is None else extra_args
    seed = extra_args.get("seed", None)
    noise_sampler = default_noise_sampler(x, seed=seed) if noise_sampler is None else noise_sampler
    s_in = x.new_ones([x.shape[0]])

    model_sampling = model.inner_model.model_patcher.get_model_object("model_sampling")
    sigmas = offset_first_sigma_for_snr(sigmas, model_sampling)
    lambdas = sigma_to_half_log_snr(sigmas, model_sampling=model_sampling)

    if tau_func is None:
        # Use default interval for stochastic sampling
        start_sigma = model_sampling.percent_to_sigma(0.2)
        end_sigma = model_sampling.percent_to_sigma(0.8)
        tau_func = sa_solver.get_tau_interval_func(start_sigma, end_sigma, eta=1.0)

    max_used_order = max(predictor_order, corrector_order)
    x_pred = x  # x: current state, x_pred: predicted next state

    h = 0.0
    tau_t = 0.0
    noise = 0.0
    pred_list = []

    # Lower order near the end to improve stability
    lower_order_to_end = sigmas[-1].item() == 0

    for i in trange(len(sigmas) - 1, disable=disable):
        # Evaluation
        denoised = model(x_pred, sigmas[i] * s_in, **extra_args)
        if callback is not None:
            callback({"x": x_pred, "i": i, "sigma": sigmas[i], "sigma_hat": sigmas[i], "denoised": denoised})
        pred_list.append(denoised)
        pred_list = pred_list[-max_used_order:]

        predictor_order_used = min(predictor_order, len(pred_list))
        if i == 0 or (sigmas[i + 1] == 0 and not use_pece):
            corrector_order_used = 0
        else:
            corrector_order_used = min(corrector_order, len(pred_list))

        if lower_order_to_end:
            predictor_order_used = min(predictor_order_used, len(sigmas) - 2 - i)
            corrector_order_used = min(corrector_order_used, len(sigmas) - 1 - i)

        # Corrector
        if corrector_order_used == 0:
            # Update by the predicted state
            x = x_pred
        else:
            curr_lambdas = lambdas[i - corrector_order_used + 1:i + 1]
            b_coeffs = sa_solver.compute_stochastic_adams_b_coeffs(
                sigmas[i],
                curr_lambdas,
                lambdas[i - 1],
                lambdas[i],
                tau_t,
                simple_order_2,
                is_corrector_step=True,
            )
            pred_mat = torch.stack(pred_list[-corrector_order_used:], dim=1)    # (B, K, ...)
            corr_res = torch.tensordot(pred_mat, b_coeffs, dims=([1], [0]))  # (B, ...)
            x = sigmas[i] / sigmas[i - 1] * (-(tau_t ** 2) * h).exp() * x + corr_res

            if tau_t > 0 and s_noise > 0:
                # The noise from the previous predictor step
                x = x + noise

            if use_pece:
                # Evaluate the corrected state
                denoised = model(x, sigmas[i] * s_in, **extra_args)
                pred_list[-1] = denoised

        # Predictor
        if sigmas[i + 1] == 0:
            # Denoising step
            x_pred = denoised
        else:
            tau_t = tau_func(sigmas[i + 1])
            curr_lambdas = lambdas[i - predictor_order_used + 1:i + 1]
            b_coeffs = sa_solver.compute_stochastic_adams_b_coeffs(
                sigmas[i + 1],
                curr_lambdas,
                lambdas[i],
                lambdas[i + 1],
                tau_t,
                simple_order_2,
                is_corrector_step=False,
            )
            pred_mat = torch.stack(pred_list[-predictor_order_used:], dim=1)    # (B, K, ...)
            pred_res = torch.tensordot(pred_mat, b_coeffs, dims=([1], [0]))  # (B, ...)
            h = lambdas[i + 1] - lambdas[i]
            x_pred = sigmas[i + 1] / sigmas[i] * (-(tau_t ** 2) * h).exp() * x + pred_res

            if tau_t > 0 and s_noise > 0:
                noise = noise_sampler(sigmas[i], sigmas[i + 1]) * sigmas[i + 1] * (-2 * tau_t ** 2 * h).expm1().neg().sqrt() * s_noise
                x_pred = x_pred + noise
    return x_pred