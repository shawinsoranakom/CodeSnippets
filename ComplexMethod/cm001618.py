def initialize(self, p) -> dict:
        self.p = p
        self.model_wrap_cfg.p = p
        self.model_wrap_cfg.mask = p.mask if hasattr(p, 'mask') else None
        self.model_wrap_cfg.nmask = p.nmask if hasattr(p, 'nmask') else None
        self.model_wrap_cfg.step = 0
        self.model_wrap_cfg.image_cfg_scale = getattr(p, 'image_cfg_scale', None)
        self.eta = p.eta if p.eta is not None else getattr(opts, self.eta_option_field, 0.0)
        self.s_min_uncond = getattr(p, 's_min_uncond', 0.0)

        k_diffusion.sampling.torch = TorchHijack(p)

        extra_params_kwargs = {}
        for param_name in self.extra_params:
            if hasattr(p, param_name) and param_name in inspect.signature(self.func).parameters:
                extra_params_kwargs[param_name] = getattr(p, param_name)

        if 'eta' in inspect.signature(self.func).parameters:
            if self.eta != self.eta_default:
                p.extra_generation_params[self.eta_infotext_field] = self.eta

            extra_params_kwargs['eta'] = self.eta

        if len(self.extra_params) > 0:
            s_churn = getattr(opts, 's_churn', p.s_churn)
            s_tmin = getattr(opts, 's_tmin', p.s_tmin)
            s_tmax = getattr(opts, 's_tmax', p.s_tmax) or self.s_tmax # 0 = inf
            s_noise = getattr(opts, 's_noise', p.s_noise)

            if 's_churn' in extra_params_kwargs and s_churn != self.s_churn:
                extra_params_kwargs['s_churn'] = s_churn
                p.s_churn = s_churn
                p.extra_generation_params['Sigma churn'] = s_churn
            if 's_tmin' in extra_params_kwargs and s_tmin != self.s_tmin:
                extra_params_kwargs['s_tmin'] = s_tmin
                p.s_tmin = s_tmin
                p.extra_generation_params['Sigma tmin'] = s_tmin
            if 's_tmax' in extra_params_kwargs and s_tmax != self.s_tmax:
                extra_params_kwargs['s_tmax'] = s_tmax
                p.s_tmax = s_tmax
                p.extra_generation_params['Sigma tmax'] = s_tmax
            if 's_noise' in extra_params_kwargs and s_noise != self.s_noise:
                extra_params_kwargs['s_noise'] = s_noise
                p.s_noise = s_noise
                p.extra_generation_params['Sigma noise'] = s_noise

        return extra_params_kwargs