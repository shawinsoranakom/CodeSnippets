def sample_ipndm(model, x, sigmas, extra_args=None, callback=None, disable=None, max_order=4):
    extra_args = {} if extra_args is None else extra_args
    s_in = x.new_ones([x.shape[0]])

    x_next = x

    buffer_model = []
    for i in trange(len(sigmas) - 1, disable=disable):
        t_cur = sigmas[i]
        t_next = sigmas[i + 1]

        x_cur = x_next

        denoised = model(x_cur, t_cur * s_in, **extra_args)
        if callback is not None:
            callback({'x': x, 'i': i, 'sigma': sigmas[i], 'sigma_hat': sigmas[i], 'denoised': denoised})

        d_cur = (x_cur - denoised) / t_cur

        order = min(max_order, i+1)
        if t_next == 0:     # Denoising step
            x_next = denoised
        elif order == 1:    # First Euler step.
            x_next = x_cur + (t_next - t_cur) * d_cur
        elif order == 2:    # Use one history point.
            x_next = x_cur + (t_next - t_cur) * (3 * d_cur - buffer_model[-1]) / 2
        elif order == 3:    # Use two history points.
            x_next = x_cur + (t_next - t_cur) * (23 * d_cur - 16 * buffer_model[-1] + 5 * buffer_model[-2]) / 12
        elif order == 4:    # Use three history points.
            x_next = x_cur + (t_next - t_cur) * (55 * d_cur - 59 * buffer_model[-1] + 37 * buffer_model[-2] - 9 * buffer_model[-3]) / 24

        if len(buffer_model) == max_order - 1:
            for k in range(max_order - 2):
                buffer_model[k] = buffer_model[k+1]
            buffer_model[-1] = d_cur
        else:
            buffer_model.append(d_cur)

    return x_next