def __init__(self, config=None):
        super(Vocoder, self).__init__()

        if config is None:
            config = self.get_default_config()

        resblock_kernel_sizes = config.get("resblock_kernel_sizes", [3, 7, 11])
        upsample_rates = config.get("upsample_rates", [5, 4, 2, 2, 2])
        upsample_kernel_sizes = config.get("upsample_kernel_sizes", [16, 16, 8, 4, 4])
        resblock_dilation_sizes = config.get("resblock_dilation_sizes", [[1, 3, 5], [1, 3, 5], [1, 3, 5]])
        upsample_initial_channel = config.get("upsample_initial_channel", 1024)
        stereo = config.get("stereo", True)
        activation = config.get("activation", "snake")
        use_bias_at_final = config.get("use_bias_at_final", True)


        # "output_sample_rate" is not present in recent checkpoint configs.
        # When absent (None), AudioVAE.output_sample_rate computes it as:
        #   sample_rate * vocoder.upsample_factor / mel_hop_length
        # where upsample_factor = product of all upsample stride lengths,
        # and mel_hop_length is loaded from the autoencoder config at
        # preprocessing.stft.hop_length (see CausalAudioAutoencoder).
        self.output_sample_rate = config.get("output_sample_rate")
        self.resblock = config.get("resblock", "1")
        self.use_tanh_at_final = config.get("use_tanh_at_final", True)
        self.apply_final_activation = config.get("apply_final_activation", True)
        self.num_kernels = len(resblock_kernel_sizes)
        self.num_upsamples = len(upsample_rates)

        in_channels = 128 if stereo else 64
        self.conv_pre = ops.Conv1d(in_channels, upsample_initial_channel, 7, 1, padding=3)

        if self.resblock == "1":
            resblock_cls = ResBlock1
        elif self.resblock == "2":
            resblock_cls = ResBlock2
        elif self.resblock == "AMP1":
            resblock_cls = AMPBlock1
        else:
            raise ValueError(f"Unknown resblock type: {self.resblock}")

        self.ups = nn.ModuleList()
        for i, (u, k) in enumerate(zip(upsample_rates, upsample_kernel_sizes)):
            self.ups.append(
                ops.ConvTranspose1d(
                    upsample_initial_channel // (2**i),
                    upsample_initial_channel // (2 ** (i + 1)),
                    k,
                    u,
                    padding=(k - u) // 2,
                )
            )

        self.resblocks = nn.ModuleList()
        for i in range(len(self.ups)):
            ch = upsample_initial_channel // (2 ** (i + 1))
            for k, d in zip(resblock_kernel_sizes, resblock_dilation_sizes):
                if self.resblock == "AMP1":
                    self.resblocks.append(resblock_cls(ch, k, d, activation=activation))
                else:
                    self.resblocks.append(resblock_cls(ch, k, d))

        out_channels = 2 if stereo else 1
        if self.resblock == "AMP1":
            act_cls = SnakeBeta if activation == "snakebeta" else Snake
            self.act_post = Activation1d(act_cls(ch))
        else:
            self.act_post = nn.LeakyReLU()

        self.conv_post = ops.Conv1d(
            ch, out_channels, 7, 1, padding=3, bias=use_bias_at_final
        )

        self.upsample_factor = np.prod([self.ups[i].stride[0] for i in range(len(self.ups))])