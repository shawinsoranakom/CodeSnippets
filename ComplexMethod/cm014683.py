def _2d_to_blocked_scaled(X, K, G, offs, format):
            xh_list = []
            xq_list = []
            x_scale_list = []
            x_global_scale_list = []
            for i in range(G):
                prev_group_end = 0 if i == 0 else input_group_end_offsets[i - 1]
                curr_group_end = input_group_end_offsets[i]
                group_size = curr_group_end - prev_group_end
                if group_size > 0:
                    x_slice = X[prev_group_end:curr_group_end, :]
                    if format == "mxfp8":
                        xh, xq, x_scale = _convert_to_mxfp8_with_hp_ref(x_slice)
                    elif format == "nvfp4":
                        xh, xq, x_scale, x_global_scale = _convert_to_nvfp4_with_hp_ref(x_slice)
                        x_global_scale_list.append(x_global_scale)
                    elif format == "mxfp4":
                        xh, xq, x_scale = _convert_to_mxfp4_with_hp_ref(x_slice)
                    else:
                        raise ValueError(f'format must be mxfp8|nvfp4|mxfp4, got "{format}"')

                    if torch.version.cuda:
                        x_scale = to_blocked(x_scale)
                    xh_list.append(xh)
                    xq_list.append(xq)
                    x_scale_list.append(x_scale)
            xh = torch.cat(xh_list, dim=0).contiguous()
            xq = torch.cat(xq_list, dim=0).contiguous()
            x_scale = torch.cat(x_scale_list, dim=0).contiguous()
            x_scale = x_scale.reshape(-1, K // block_size)
            xq = xq.view(-1, xq.shape[-1])
            xh = xh.view(-1, xh.shape[-1])

            x_global_scales = None
            if len(x_global_scale_list) > 0:
                x_global_scales = torch.stack(x_global_scale_list)

            return xh, xq, x_scale, x_global_scales