def __init__(
            self,
            in_channels=640,
            out_channels=133,
            input_size=(768, 1024),
            heatmap_scale=4,
            deconv_out_channels=(640,),
            deconv_kernel_sizes=(4,),
            conv_out_channels=(640,),
            conv_kernel_sizes=(1,),
            final_layer_kernel_size=1,
            device=None, dtype=None, operations=None
        ):
        super().__init__()

        self.heatmap_size = (input_size[0] // heatmap_scale, input_size[1] // heatmap_scale)
        self.scale_factor = ((np.array(input_size) - 1) / (np.array(self.heatmap_size) - 1)).astype(np.float32)

        # Deconv layers
        if deconv_out_channels:
            deconv_layers = []
            for out_ch, kernel_size in zip(deconv_out_channels, deconv_kernel_sizes):
                if kernel_size == 4:
                    padding, output_padding = 1, 0
                elif kernel_size == 3:
                    padding, output_padding = 1, 1
                elif kernel_size == 2:
                    padding, output_padding = 0, 0
                else:
                    raise ValueError(f'Unsupported kernel size {kernel_size}')

                deconv_layers.extend([
                    operations.ConvTranspose2d(in_channels, out_ch, kernel_size,
                                     stride=2, padding=padding, output_padding=output_padding, bias=False, device=device, dtype=dtype),
                    torch.nn.InstanceNorm2d(out_ch, device=device, dtype=dtype),
                    torch.nn.SiLU(inplace=True)
                ])
                in_channels = out_ch
            self.deconv_layers = torch.nn.Sequential(*deconv_layers)
        else:
            self.deconv_layers = torch.nn.Identity()

        # Conv layers
        if conv_out_channels:
            conv_layers = []
            for out_ch, kernel_size in zip(conv_out_channels, conv_kernel_sizes):
                padding = (kernel_size - 1) // 2
                conv_layers.extend([
                    operations.Conv2d(in_channels, out_ch, kernel_size,
                            stride=1, padding=padding, device=device, dtype=dtype),
                    torch.nn.InstanceNorm2d(out_ch, device=device, dtype=dtype),
                    torch.nn.SiLU(inplace=True)
                ])
                in_channels = out_ch
            self.conv_layers = torch.nn.Sequential(*conv_layers)
        else:
            self.conv_layers = torch.nn.Identity()

        self.final_layer = operations.Conv2d(in_channels, out_channels, kernel_size=final_layer_kernel_size, padding=final_layer_kernel_size // 2, device=device, dtype=dtype)