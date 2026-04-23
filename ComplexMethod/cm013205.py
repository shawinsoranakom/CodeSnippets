def sample_inputs_interpolate(mode, self, device, dtype, requires_grad, **kwargs):
    N, C = 2, 3
    D = 4
    S = 3
    L = 5

    align_corners_options: tuple[Any, ...] = (None,)
    if mode in ('linear', 'bilinear', 'bicubic', 'trilinear'):
        align_corners_options = (True, False, None)
    ranks_for_mode = {
        'nearest': [1, 2, 3],
        'nearest-exact': [1, 2, 3],
        'linear': [1],
        'bilinear': [2],
        'bicubic': [2],
        'trilinear': [3],
        'area': [1, 2, 3]
    }

    def shape(size, rank, with_batch_channel=True):
        if with_batch_channel:
            return tuple([N, C] + ([size] * rank))
        return tuple([size] * rank)

    def uneven_shape(size, rank, with_batch_channel=True):
        rc = list(shape(size, rank, with_batch_channel))
        rc[-1] += 1
        if rank > 2:
            rc[-2] -= 1
        return tuple(rc)

    if mode in ('bilinear', 'bicubic') and dtype == torch.uint8:
        make_arg = partial(
            make_tensor,
            device=device,
            dtype=dtype,
            requires_grad=requires_grad,
            # we pick more realistic upper bound 256 instead of default 10 for uint8 dtype
            high=256 if dtype == torch.uint8 else None,
        )
        # provide few samples for a more close to typical image processing usage
        rank = 2
        for memory_format in [torch.contiguous_format, torch.channels_last]:
            yield SampleInput(
                make_arg(shape(270, rank), memory_format=memory_format),
                shape(130, rank, False),
                scale_factor=None,
                mode=mode,
                align_corners=False,
            )

    make_arg = partial(make_tensor, device=device, dtype=dtype, requires_grad=requires_grad)

    for align_corners in align_corners_options:
        for rank in ranks_for_mode[mode]:
            yield SampleInput(
                make_arg(shape(D, rank)),
                shape(S, rank, False),
                scale_factor=None,
                mode=mode,
                align_corners=align_corners,
            )
            yield SampleInput(
                make_arg(shape(D, rank)),
                shape(L, rank, False),
                scale_factor=None,
                mode=mode,
                align_corners=align_corners,
            )
            if rank > 1 and dtype.is_floating_point:
                yield SampleInput(
                    make_arg(uneven_shape(D, rank)),
                    uneven_shape(S, rank, False),
                    scale_factor=None,
                    mode=mode,
                    align_corners=align_corners,
                )
                yield SampleInput(
                    make_arg(uneven_shape(D, rank)),
                    uneven_shape(L, rank, False),
                    scale_factor=None,
                    mode=mode,
                    align_corners=align_corners,
                )
            for recompute_scale_factor in [False, True]:
                for scale_factor in [1.7, 0.6]:
                    yield SampleInput(
                        make_arg(shape(D, rank)),
                        size=None,
                        scale_factor=scale_factor,
                        mode=mode,
                        align_corners=align_corners,
                        recompute_scale_factor=recompute_scale_factor,
                    )