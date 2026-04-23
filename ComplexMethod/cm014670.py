def _2d_grouped_tensor_to_blocked_scaled(t, MN, G, offs, format='mxfp8'):
    # Convert scales to blocked format. either mxfp8 or nvfp4
    th_list = []
    t_list = []
    t_blocked_scale_list = []
    t_global_scale_list = []

    def round_up(x: int, y: int) -> int:
        return ((x + y - 1) // y) * y

    for group_idx in range(G):
        # to_mxfp8 per group
        prev_group_end_offset = (
            0 if group_idx == 0 else offs[group_idx - 1]
        )
        curr_group_end_offset = offs[group_idx]
        group_size = curr_group_end_offset - prev_group_end_offset
        if group_size > 0:
            t_slice = t[
                :, prev_group_end_offset:curr_group_end_offset
            ].contiguous()  # (M, K_group)
            if format == 'mxfp8':
                th_slice, tq_slice, t_scale_slice = _convert_to_mxfp8_with_hp_ref(t_slice)
            elif format == 'nvfp4':
                th_slice, tq_slice, t_scale_slice, tq_global = _convert_to_nvfp4_with_hp_ref(
                    t_slice,
                )
                t_global_scale_list.append(tq_global)
            elif format == 'mxfp4':
                th_slice, tq_slice, t_scale_slice = _convert_to_mxfp4_with_hp_ref(t_slice)
            else:
                raise ValueError(f'format must be mxfp8|nvfp4, got "{format}"')
            t_list.append(tq_slice)
            th_list.append(th_slice)

            # Convert scales to blocked format.
            if torch.version.cuda:
                t_scale_slice_blocked = to_blocked(
                    t_scale_slice
                )  # (round_up(M, 128), round_up(K_group//32, 4))
            t_blocked_scale_list.append(t_scale_slice_blocked)

    # Assemble the full XQ and WQ
    tq = torch.cat(t_list, dim=1).contiguous()
    th = torch.cat(th_list, dim=1).contiguous()

    # Combine all XQ groups blocked scales into one tensor.
    t_blocked_scales = torch.cat(t_blocked_scale_list, dim=0)
    MN_rounded = round_up(MN, 128)
    t_blocked_scales = t_blocked_scales.reshape(MN_rounded, -1)

    # Global scales only exist for nvfp4
    t_global_scales = None
    if len(t_global_scale_list) > 0:
        t_global_scales = torch.stack(t_global_scale_list)

    return th, tq, t_blocked_scales, t_global_scales