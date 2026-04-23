def get_deis_coeff_list(t_steps, max_order, N=10000, deis_mode='tab'):
    """
    Get the coefficient list for DEIS sampling.

    Args:
        t_steps: A pytorch tensor. The time steps for sampling.
        max_order: A `int`. Maximum order of the solver. 1 <= max_order <= 4
        N: A `int`. Use how many points to perform the numerical integration when deis_mode=='tab'.
        deis_mode: A `str`. Select between 'tab' and 'rhoab'. Type of DEIS.
    Returns:
        A pytorch tensor. A batch of generated samples or sampling trajectories if return_inters=True.
    """
    if deis_mode == 'tab':
        t_steps, beta_0, beta_1 = edm2t(t_steps)
        C = []
        for i, (t_cur, t_next) in enumerate(zip(t_steps[:-1], t_steps[1:])):
            order = min(i+1, max_order)
            if order == 1:
                C.append([])
            else:
                taus = torch.linspace(t_cur, t_next, N)   # split the interval for integral appximation
                dtau = (t_next - t_cur) / N
                prev_t = t_steps[[i - k for k in range(order)]]
                coeff_temp = []
                integrand = cal_intergrand(beta_0, beta_1, taus)
                for j in range(order):
                    poly = cal_poly(prev_t, j, taus)
                    coeff_temp.append(torch.sum(integrand * poly) * dtau)
                C.append(coeff_temp)

    elif deis_mode == 'rhoab':
        # Analytical solution, second order
        def get_def_intergral_2(a, b, start, end, c):
            coeff = (end**3 - start**3) / 3 - (end**2 - start**2) * (a + b) / 2 + (end - start) * a * b
            return coeff / ((c - a) * (c - b))

        # Analytical solution, third order
        def get_def_intergral_3(a, b, c, start, end, d):
            coeff = (end**4 - start**4) / 4 - (end**3 - start**3) * (a + b + c) / 3 \
                    + (end**2 - start**2) * (a*b + a*c + b*c) / 2 - (end - start) * a * b * c
            return coeff / ((d - a) * (d - b) * (d - c))

        C = []
        for i, (t_cur, t_next) in enumerate(zip(t_steps[:-1], t_steps[1:])):
            order = min(i, max_order)
            if order == 0:
                C.append([])
            else:
                prev_t = t_steps[[i - k for k in range(order+1)]]
                if order == 1:
                    coeff_cur = ((t_next - prev_t[1])**2 - (t_cur - prev_t[1])**2) / (2 * (t_cur - prev_t[1]))
                    coeff_prev1 = (t_next - t_cur)**2 / (2 * (prev_t[1] - t_cur))
                    coeff_temp = [coeff_cur, coeff_prev1]
                elif order == 2:
                    coeff_cur = get_def_intergral_2(prev_t[1], prev_t[2], t_cur, t_next, t_cur)
                    coeff_prev1 = get_def_intergral_2(t_cur, prev_t[2], t_cur, t_next, prev_t[1])
                    coeff_prev2 = get_def_intergral_2(t_cur, prev_t[1], t_cur, t_next, prev_t[2])
                    coeff_temp = [coeff_cur, coeff_prev1, coeff_prev2]
                elif order == 3:
                    coeff_cur = get_def_intergral_3(prev_t[1], prev_t[2], prev_t[3], t_cur, t_next, t_cur)
                    coeff_prev1 = get_def_intergral_3(t_cur, prev_t[2], prev_t[3], t_cur, t_next, prev_t[1])
                    coeff_prev2 = get_def_intergral_3(t_cur, prev_t[1], prev_t[3], t_cur, t_next, prev_t[2])
                    coeff_prev3 = get_def_intergral_3(t_cur, prev_t[1], prev_t[2], t_cur, t_next, prev_t[3])
                    coeff_temp = [coeff_cur, coeff_prev1, coeff_prev2, coeff_prev3]
                C.append(coeff_temp)
    return C