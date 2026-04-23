def __init__(self, latent_channels, parallel=False, encoder_time_downscale=(True, True, False), decoder_time_upscale=(False, True, True), decoder_space_upscale=(True, True, True),
                 latent_format=None, show_progress_bar=False):
        super().__init__()
        self.image_channels = 3
        self.patch_size = 1
        self.latent_channels = latent_channels
        self.parallel = parallel
        self.latent_format = latent_format
        self.show_progress_bar = show_progress_bar
        self.process_in = latent_format().process_in if latent_format is not None else (lambda x: x)
        self.process_out = latent_format().process_out if latent_format is not None else (lambda x: x)
        if self.latent_channels in [48, 32]: # Wan 2.2 and HunyuanVideo1.5
            self.patch_size = 2
        elif self.latent_channels == 128: # LTX2
            self.patch_size, self.latent_channels, encoder_time_downscale, decoder_time_upscale = 4, 128, (True, True, True), (True, True, True)

        if self.latent_channels == 32: # HunyuanVideo1.5
            act_func = nn.LeakyReLU(0.2, inplace=True)
        else: # HunyuanVideo, Wan 2.1
            act_func = nn.ReLU(inplace=True)

        self.encoder = nn.Sequential(
            conv(self.image_channels*self.patch_size**2, 64), act_func,
            TPool(64, 2 if encoder_time_downscale[0] else 1), conv(64, 64, stride=2, bias=False), MemBlock(64, 64, act_func), MemBlock(64, 64, act_func), MemBlock(64, 64, act_func),
            TPool(64, 2 if encoder_time_downscale[1] else 1), conv(64, 64, stride=2, bias=False), MemBlock(64, 64, act_func), MemBlock(64, 64, act_func), MemBlock(64, 64, act_func),
            TPool(64, 2 if encoder_time_downscale[2] else 1), conv(64, 64, stride=2, bias=False), MemBlock(64, 64, act_func), MemBlock(64, 64, act_func), MemBlock(64, 64, act_func),
            conv(64, self.latent_channels),
        )
        n_f = [256, 128, 64, 64]

        self.decoder = nn.Sequential(
            Clamp(), conv(self.latent_channels, n_f[0]), act_func,
            MemBlock(n_f[0], n_f[0], act_func), MemBlock(n_f[0], n_f[0], act_func), MemBlock(n_f[0], n_f[0], act_func), nn.Upsample(scale_factor=2 if decoder_space_upscale[0] else 1), TGrow(n_f[0], 2 if decoder_time_upscale[0] else 1), conv(n_f[0], n_f[1], bias=False),
            MemBlock(n_f[1], n_f[1], act_func), MemBlock(n_f[1], n_f[1], act_func), MemBlock(n_f[1], n_f[1], act_func), nn.Upsample(scale_factor=2 if decoder_space_upscale[1] else 1), TGrow(n_f[1], 2 if decoder_time_upscale[1] else 1), conv(n_f[1], n_f[2], bias=False),
            MemBlock(n_f[2], n_f[2], act_func), MemBlock(n_f[2], n_f[2], act_func), MemBlock(n_f[2], n_f[2], act_func), nn.Upsample(scale_factor=2 if decoder_space_upscale[2] else 1), TGrow(n_f[2], 2 if decoder_time_upscale[2] else 1), conv(n_f[2], n_f[3], bias=False),
            act_func, conv(n_f[3], self.image_channels*self.patch_size**2),
        )

        self.t_downscale = 2**sum(t.stride == 2 for t in self.encoder if isinstance(t, TPool))
        self.t_upscale = 2**sum(t.stride == 2 for t in self.decoder if isinstance(t, TGrow))
        self.frames_to_trim = self.t_upscale - 1
        self._show_progress_bar = show_progress_bar