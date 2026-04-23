def model_fn(x, t_continuous, condition, unconditional_condition):
        """
        The noise prediction model function that is used for DPM-Solver.
        """
        if t_continuous.reshape((-1,)).shape[0] == 1:
            t_continuous = t_continuous.expand((x.shape[0]))
        if guidance_type == "uncond":
            return noise_pred_fn(x, t_continuous)
        elif guidance_type == "classifier":
            assert classifier_fn is not None
            t_input = get_model_input_time(t_continuous)
            cond_grad = cond_grad_fn(x, t_input, condition)
            sigma_t = noise_schedule.marginal_std(t_continuous)
            noise = noise_pred_fn(x, t_continuous)
            return noise - guidance_scale * expand_dims(sigma_t, dims=cond_grad.dim()) * cond_grad
        elif guidance_type == "classifier-free":
            if guidance_scale == 1. or unconditional_condition is None:
                return noise_pred_fn(x, t_continuous, cond=condition)
            else:
                x_in = torch.cat([x] * 2)
                t_in = torch.cat([t_continuous] * 2)
                if isinstance(condition, dict):
                    assert isinstance(unconditional_condition, dict)
                    c_in = {}
                    for k in condition:
                        if isinstance(condition[k], list):
                            c_in[k] = [torch.cat([
                                unconditional_condition[k][i],
                                condition[k][i]]) for i in range(len(condition[k]))]
                        else:
                            c_in[k] = torch.cat([
                                unconditional_condition[k],
                                condition[k]])
                elif isinstance(condition, list):
                    c_in = []
                    assert isinstance(unconditional_condition, list)
                    for i in range(len(condition)):
                        c_in.append(torch.cat([unconditional_condition[i], condition[i]]))
                else:
                    c_in = torch.cat([unconditional_condition, condition])
                noise_uncond, noise = noise_pred_fn(x_in, t_in, cond=c_in).chunk(2)
                return noise_uncond + guidance_scale * (noise - noise_uncond)