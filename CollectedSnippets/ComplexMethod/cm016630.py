def sample(self, x, timesteps, t_start=None, t_end=None, order=3, skip_type='time_uniform',
        method='singlestep', lower_order_final=True, denoise_to_zero=False, solver_type='dpm_solver',
        atol=0.0078, rtol=0.05, corrector=False, callback=None, disable_pbar=False
    ):
        # t_0 = 1. / self.noise_schedule.total_N if t_end is None else t_end
        # t_T = self.noise_schedule.T if t_start is None else t_start
        steps = len(timesteps) - 1
        if method == 'multistep':
            assert steps >= order
            # timesteps = self.get_time_steps(skip_type=skip_type, t_T=t_T, t_0=t_0, N=steps, device=device)
            assert timesteps.shape[0] - 1 == steps
            # with torch.no_grad():
            for step_index in trange(steps, disable=disable_pbar):
                if step_index == 0:
                    vec_t = timesteps[0].expand((x.shape[0]))
                    model_prev_list = [self.model_fn(x, vec_t)]
                    t_prev_list = [vec_t]
                elif step_index < order:
                    init_order = step_index
                # Init the first `order` values by lower order multistep DPM-Solver.
                # for init_order in range(1, order):
                    vec_t = timesteps[init_order].expand(x.shape[0])
                    x, model_x = self.multistep_uni_pc_update(x, model_prev_list, t_prev_list, vec_t, init_order, use_corrector=True)
                    if model_x is None:
                        model_x = self.model_fn(x, vec_t)
                    model_prev_list.append(model_x)
                    t_prev_list.append(vec_t)
                else:
                    extra_final_step = 0
                    if step_index == (steps - 1):
                        extra_final_step = 1
                    for step in range(step_index, step_index + 1 + extra_final_step):
                        vec_t = timesteps[step].expand(x.shape[0])
                        if lower_order_final:
                            step_order = min(order, steps + 1 - step)
                        else:
                            step_order = order
                        # print('this step order:', step_order)
                        if step == steps:
                            # print('do not run corrector at the last step')
                            use_corrector = False
                        else:
                            use_corrector = True
                        x, model_x =  self.multistep_uni_pc_update(x, model_prev_list, t_prev_list, vec_t, step_order, use_corrector=use_corrector)
                        for i in range(order - 1):
                            t_prev_list[i] = t_prev_list[i + 1]
                            model_prev_list[i] = model_prev_list[i + 1]
                        t_prev_list[-1] = vec_t
                        # We do not need to evaluate the final model value.
                        if step < steps:
                            if model_x is None:
                                model_x = self.model_fn(x, vec_t)
                            model_prev_list[-1] = model_x
                if callback is not None:
                    callback({'x': x, 'i': step_index, 'denoised': model_prev_list[-1]})
        else:
            raise NotImplementedError()
        # if denoise_to_zero:
        #     x = self.denoise_to_zero_fn(x, torch.ones((x.shape[0],)).to(device) * t_0)
        return x