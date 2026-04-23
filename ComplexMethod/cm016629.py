def multistep_uni_pc_bh_update(self, x, model_prev_list, t_prev_list, t, order, x_t=None, use_corrector=True):
        # print(f'using unified predictor-corrector with order {order} (solver type: B(h))')
        ns = self.noise_schedule
        assert order <= len(model_prev_list)
        dims = x.dim()

        # first compute rks
        t_prev_0 = t_prev_list[-1]
        lambda_prev_0 = ns.marginal_lambda(t_prev_0)
        lambda_t = ns.marginal_lambda(t)
        model_prev_0 = model_prev_list[-1]
        sigma_prev_0, sigma_t = ns.marginal_std(t_prev_0), ns.marginal_std(t)
        log_alpha_prev_0, log_alpha_t = ns.marginal_log_mean_coeff(t_prev_0), ns.marginal_log_mean_coeff(t)
        alpha_t = torch.exp(log_alpha_t)

        h = lambda_t - lambda_prev_0

        rks = []
        D1s = []
        for i in range(1, order):
            t_prev_i = t_prev_list[-(i + 1)]
            model_prev_i = model_prev_list[-(i + 1)]
            lambda_prev_i = ns.marginal_lambda(t_prev_i)
            rk = ((lambda_prev_i - lambda_prev_0) / h)[0]
            rks.append(rk)
            D1s.append((model_prev_i - model_prev_0) / rk)

        rks.append(1.)
        rks = torch.tensor(rks, device=x.device)

        R = []
        b = []

        hh = -h[0] if self.predict_x0 else h[0]
        h_phi_1 = torch.expm1(hh) # h\phi_1(h) = e^h - 1
        h_phi_k = h_phi_1 / hh - 1

        factorial_i = 1

        if self.variant == 'bh1':
            B_h = hh
        elif self.variant == 'bh2':
            B_h = torch.expm1(hh)
        else:
            raise NotImplementedError()

        for i in range(1, order + 1):
            R.append(torch.pow(rks, i - 1))
            b.append(h_phi_k * factorial_i / B_h)
            factorial_i *= (i + 1)
            h_phi_k = h_phi_k / hh - 1 / factorial_i

        R = torch.stack(R)
        b = torch.tensor(b, device=x.device)

        # now predictor
        use_predictor = len(D1s) > 0 and x_t is None
        if len(D1s) > 0:
            D1s = torch.stack(D1s, dim=1) # (B, K)
            if x_t is None:
                # for order 2, we use a simplified version
                if order == 2:
                    rhos_p = torch.tensor([0.5], device=b.device)
                else:
                    rhos_p = torch.linalg.solve(R[:-1, :-1], b[:-1])
        else:
            D1s = None

        if use_corrector:
            # print('using corrector')
            # for order 1, we use a simplified version
            if order == 1:
                rhos_c = torch.tensor([0.5], device=b.device)
            else:
                rhos_c = torch.linalg.solve(R, b)

        model_t = None
        if self.predict_x0:
            x_t_ = (
                expand_dims(sigma_t / sigma_prev_0, dims) * x
                - expand_dims(alpha_t * h_phi_1, dims)* model_prev_0
            )

            if x_t is None:
                if use_predictor:
                    pred_res = torch.tensordot(D1s, rhos_p, dims=([1], [0]))  # torch.einsum('k,bkchw->bchw', rhos_p, D1s)
                else:
                    pred_res = 0
                x_t = x_t_ - expand_dims(alpha_t * B_h, dims) * pred_res

            if use_corrector:
                model_t = self.model_fn(x_t, t)
                if D1s is not None:
                    corr_res = torch.tensordot(D1s, rhos_c[:-1], dims=([1], [0]))  # torch.einsum('k,bkchw->bchw', rhos_c[:-1], D1s)
                else:
                    corr_res = 0
                D1_t = (model_t - model_prev_0)
                x_t = x_t_ - expand_dims(alpha_t * B_h, dims) * (corr_res + rhos_c[-1] * D1_t)
        else:
            x_t_ = (
                expand_dims(torch.exp(log_alpha_t - log_alpha_prev_0), dims) * x
                - expand_dims(sigma_t * h_phi_1, dims) * model_prev_0
            )
            if x_t is None:
                if use_predictor:
                    pred_res = torch.einsum('k,bkchw->bchw', rhos_p, D1s)
                else:
                    pred_res = 0
                x_t = x_t_ - expand_dims(sigma_t * B_h, dims) * pred_res

            if use_corrector:
                model_t = self.model_fn(x_t, t)
                if D1s is not None:
                    corr_res = torch.einsum('k,bkchw->bchw', rhos_c[:-1], D1s)
                else:
                    corr_res = 0
                D1_t = (model_t - model_prev_0)
                x_t = x_t_ - expand_dims(sigma_t * B_h, dims) * (corr_res + rhos_c[-1] * D1_t)
        return x_t, model_t