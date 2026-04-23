def _test_conv_cudnn_nhwc_nchw(self, layer, n, c, h, w, k, filter_size, device):
        data = torch.randint(1, 10, (n, c, h, w), dtype=torch.float32, device=device)
        ref_input = data.clone().contiguous().requires_grad_(True)
        ref_conv = layer(c, k, filter_size).float().to(device)
        ref_out = ref_conv(ref_input)
        grad = torch.randint(1, 10, ref_out.size(), dtype=torch.float32, device="cuda")
        ref_out.backward(grad)

        for w_f in [torch.contiguous_format, torch.channels_last]:
            for g_f in [torch.contiguous_format, torch.channels_last]:
                for input_format in [torch.contiguous_format, torch.channels_last]:
                    output_format = torch.contiguous_format
                    if input_format == torch.channels_last:
                        output_format = torch.channels_last
                    # This is because we have N111 weight that cannot handle
                    # the ambiguous memory_format
                    if w_f == torch.channels_last:
                        if layer is nn.Conv2d and filter_size * c != 1:
                            output_format = torch.channels_last
                        if layer is nn.ConvTranspose2d and filter_size * k != 1:
                            output_format = torch.channels_last
                    self._run_conv(
                        layer,
                        device,
                        data,
                        grad,
                        ref_conv,
                        ref_input,
                        ref_out,
                        input_format,
                        w_f,
                        g_f,
                        output_format,
                    )