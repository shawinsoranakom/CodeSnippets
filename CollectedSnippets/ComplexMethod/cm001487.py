def wrapper(*args, **kwargs):
        if not params.enabled:
            return params.forward(*args, **kwargs)

        latent_tile_size = max(128, params.tile_size) // 8
        x = args[0]

        # VAE
        if x.ndim == 4:
            b, c, h, w = x.shape

            nh = random_divisor(h, latent_tile_size, params.swap_size)
            nw = random_divisor(w, latent_tile_size, params.swap_size)

            if nh * nw > 1:
                x = rearrange(x, "b c (nh h) (nw w) -> (b nh nw) c h w", nh=nh, nw=nw)  # split into nh * nw tiles

            out = params.forward(x, *args[1:], **kwargs)

            if nh * nw > 1:
                out = rearrange(out, "(b nh nw) c h w -> b c (nh h) (nw w)", nh=nh, nw=nw)

        # U-Net
        else:
            hw: int = x.size(1)
            h, w = find_hw_candidates(hw, params.aspect_ratio)
            assert h * w == hw, f"Invalid aspect ratio {params.aspect_ratio} for input of shape {x.shape}, hw={hw}, h={h}, w={w}"

            factor = 2 ** params.depth if scale_depth else 1
            nh = random_divisor(h, latent_tile_size * factor, params.swap_size)
            nw = random_divisor(w, latent_tile_size * factor, params.swap_size)

            if nh * nw > 1:
                x = rearrange(x, "b (nh h nw w) c -> (b nh nw) (h w) c", h=h // nh, w=w // nw, nh=nh, nw=nw)

            out = params.forward(x, *args[1:], **kwargs)

            if nh * nw > 1:
                out = rearrange(out, "(b nh nw) hw c -> b nh nw hw c", nh=nh, nw=nw)
                out = rearrange(out, "b nh nw (h w) c -> b (nh h nw w) c", h=h // nh, w=w // nw)

        return out