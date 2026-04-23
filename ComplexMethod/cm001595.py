def get_sigmas(self, p, steps):
        discard_next_to_last_sigma = self.config is not None and self.config.options.get('discard_next_to_last_sigma', False)
        if opts.always_discard_next_to_last_sigma and not discard_next_to_last_sigma:
            discard_next_to_last_sigma = True
            p.extra_generation_params["Discard penultimate sigma"] = True

        steps += 1 if discard_next_to_last_sigma else 0

        scheduler_name = (p.hr_scheduler if p.is_hr_pass else p.scheduler) or 'Automatic'
        if scheduler_name == 'Automatic':
            scheduler_name = self.config.options.get('scheduler', None)

        scheduler = sd_schedulers.schedulers_map.get(scheduler_name)

        m_sigma_min, m_sigma_max = self.model_wrap.sigmas[0].item(), self.model_wrap.sigmas[-1].item()
        sigma_min, sigma_max = (0.1, 10) if opts.use_old_karras_scheduler_sigmas else (m_sigma_min, m_sigma_max)

        if p.sampler_noise_scheduler_override:
            sigmas = p.sampler_noise_scheduler_override(steps)
        elif scheduler is None or scheduler.function is None:
            sigmas = self.model_wrap.get_sigmas(steps)
        else:
            sigmas_kwargs = {'sigma_min': sigma_min, 'sigma_max': sigma_max}

            if scheduler.label != 'Automatic' and not p.is_hr_pass:
                p.extra_generation_params["Schedule type"] = scheduler.label
            elif scheduler.label != p.extra_generation_params.get("Schedule type"):
                p.extra_generation_params["Hires schedule type"] = scheduler.label

            if opts.sigma_min != 0 and opts.sigma_min != m_sigma_min:
                sigmas_kwargs['sigma_min'] = opts.sigma_min
                p.extra_generation_params["Schedule min sigma"] = opts.sigma_min

            if opts.sigma_max != 0 and opts.sigma_max != m_sigma_max:
                sigmas_kwargs['sigma_max'] = opts.sigma_max
                p.extra_generation_params["Schedule max sigma"] = opts.sigma_max

            if scheduler.default_rho != -1 and opts.rho != 0 and opts.rho != scheduler.default_rho:
                sigmas_kwargs['rho'] = opts.rho
                p.extra_generation_params["Schedule rho"] = opts.rho

            if scheduler.need_inner_model:
                sigmas_kwargs['inner_model'] = self.model_wrap

            if scheduler.label == 'Beta':
                p.extra_generation_params["Beta schedule alpha"] = opts.beta_dist_alpha
                p.extra_generation_params["Beta schedule beta"] = opts.beta_dist_beta

            sigmas = scheduler.function(n=steps, **sigmas_kwargs, device=devices.cpu)

        if discard_next_to_last_sigma:
            sigmas = torch.cat([sigmas[:-2], sigmas[-1:]])

        return sigmas.cpu()