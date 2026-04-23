def forward(self, x, return_weight=False):
        """
        Args:
            x (Tensor): input image batch
            return_weight (bool): set to False by default,
                                  if set to True return the predicted offsets of AIN, denoted as x_{offsets}

        Returns:
            Tensor: rectified image [batch_size x I_channel_num x I_height x I_width], the same as the input size
        """

        if self.spt:
            feat = self.spt_convnet(x)
            fc1 = self.stucture_fc1(feat)
            sp_weight_fusion = self.stucture_fc2(fc1)
            sp_weight_fusion = sp_weight_fusion.reshape(
                [x.shape[0], self.out_weight, 1]
            )
            if self.offsets:  # SPIN w. AIN
                lambda_color = sp_weight_fusion[:, self.spt_length, 0]
                lambda_color = (
                    self.sigmoid(lambda_color).unsqueeze(-1).unsqueeze(-1).unsqueeze(-1)
                )
                sp_weight = sp_weight_fusion[:, : self.spt_length, :]
                offsets = self.pool(self.offset_fc2(self.offset_fc1(feat)))

                assert offsets.shape[2] == 2  # 2
                assert offsets.shape[3] == 6  # 16
                offsets = self.sigmoid(offsets)  # v12

                if return_weight:
                    return offsets
                offsets = nn.functional.upsample(
                    offsets, size=(x.shape[2], x.shape[3]), mode="bilinear"
                )

                if self.stn:
                    batch_C_prime = sp_weight_fusion[
                        :, (self.spt_length + 1) :, :
                    ].reshape([x.shape[0], self.F, 2])
                    build_P_prime = self.GridGenerator(batch_C_prime, self.I_r_size)
                    build_P_prime_reshape = build_P_prime.reshape(
                        [build_P_prime.shape[0], self.I_r_size[0], self.I_r_size[1], 2]
                    )

            else:  # SPIN w.o. AIN
                sp_weight = sp_weight_fusion[:, : self.spt_length, :]
                lambda_color, offsets = None, None

                if self.stn:
                    batch_C_prime = sp_weight_fusion[:, self.spt_length :, :].reshape(
                        [x.shape[0], self.F, 2]
                    )
                    build_P_prime = self.GridGenerator(batch_C_prime, self.I_r_size)
                    build_P_prime_reshape = build_P_prime.reshape(
                        [build_P_prime.shape[0], self.I_r_size[0], self.I_r_size[1], 2]
                    )

            x = self.sp_net(x, sp_weight, offsets, lambda_color)
            if self.stn:
                is_fp16 = False
                if build_P_prime_reshape.dtype != paddle.float32:
                    data_type = build_P_prime_reshape.dtype
                    x = x.cast(paddle.float32)
                    build_P_prime_reshape = build_P_prime_reshape.cast(paddle.float32)
                    is_fp16 = True
                x = F.grid_sample(
                    x=x, grid=build_P_prime_reshape, padding_mode="border"
                )
                if is_fp16:
                    x = x.cast(data_type)
        return x