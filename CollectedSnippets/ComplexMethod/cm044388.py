def _upscale_block(self,
                       inputs: KerasTensor,
                       filters: int,
                       skip_residual: bool = False,
                       is_mask: bool = False) -> KerasTensor:
        """ Upscale block for Phaze-A Decoder.

        Uses requested upscale method, adds requested regularization and activation function.

        Parameters
        ----------
        inputs: :class:`keras.KerasTensor`
            The input tensor for the upscale block
        filters: int
            The number of filters to use for the upscale
        skip_residual: bool, optional
            ``True`` if a residual block should not be placed in the upscale block, otherwise
            ``False``. Default ``False``
        is_mask: bool, optional
            ``True`` if the input is a mask. ``False`` if the input is a face. Default: ``False``

        Returns
        -------
        :class:`keras.KerasTensor`
            The output tensor from the upscale block
        """
        upscaler = _get_upscale_layer(T.cast(T.Literal["resize_images", "subpixel", "upscale_dny",
                                                       "upscale_fast", "upscale_hybrid",
                                                       "upsample2d"],
                                             cfg.dec_upscale_method()),
                                      filters,
                                      activation="leakyrelu",
                                      upsamples=2,
                                      interpolation="bilinear")

        var_x = upscaler(inputs)
        if not is_mask and cfg.dec_gaussian():
            var_x = kl.GaussianNoise(1.0)(var_x)
        if not is_mask and cfg.dec_res_blocks() and not skip_residual:
            var_x = self._normalization(var_x)
            var_x = kl.LeakyReLU(negative_slope=0.2)(var_x)
            for _ in range(cfg.dec_res_blocks()):
                var_x = ResidualBlock(filters)(var_x)
        else:
            var_x = self._normalization(var_x)
            if not self._is_dny:
                var_x = kl.LeakyReLU(negative_slope=0.1)(var_x)
        return var_x