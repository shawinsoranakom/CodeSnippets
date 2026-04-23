def __call__(self, inputs: KerasTensor | list[KerasTensor]) -> KerasTensor | list[KerasTensor]:
        """ Upscale Network.

        Parameters
        inputs: :class:`keras.KerasTensor` | list[:class:`keras.KerasTensor`]
            Input tensor(s) to upscale block. This will be a single tensor if learn mask is not
            selected or if this is the first call to the upscale blocks. If learn mask is selected
            and this is not the first call to upscale blocks, then this will be a list of the face
            and mask tensors.

        Returns
        -------
         :class:`keras.KerasTensor` | list[:class:`keras.KerasTensor`]
            The output of encoder blocks. Either a single tensor (if learn mask is not enabled) or
            list of tensors (if learn mask is enabled)
        """
        start_idx, end_idx = (0, None) if self._layer_indicies is None else self._layer_indicies
        end_idx = None if end_idx == -1 else end_idx

        var_x: KerasTensor
        var_y: KerasTensor
        if cfg_loss.learn_mask() and start_idx == 0:
            # Mask needs to be created
            var_x = inputs
            var_y = inputs
        elif cfg_loss.learn_mask():
            # Mask has already been created and is an input to upscale blocks
            var_x, var_y = inputs
        else:
            # No mask required
            var_x = inputs

        if start_idx == 0:
            var_x = self._reshape_for_output(var_x)

            if cfg_loss.learn_mask():
                var_y = self._reshape_for_output(var_y)

            if self._is_dny:
                var_x = self._dny_entry(var_x)
            if self._is_dny and cfg_loss.learn_mask():
                var_y = self._dny_entry(var_y)

        # De-convolve
        if not self._filters:
            upscales = int(np.log2(cfg.output_size() / var_x.shape[1]))
            self._filters.extend(_get_curve(cfg.dec_max_filters(),
                                            cfg.dec_min_filters(),
                                            upscales,
                                            cfg.dec_filter_slope(),
                                            mode=T.cast(T.Literal["full", "cap_min", "cap_max"],
                                                        cfg.dec_slope_mode())))
            logger.debug("Generated class filters: %s", self._filters)

        filters = self._filters[start_idx: end_idx]

        for idx, filts in enumerate(filters):
            skip_res = idx == len(filters) - 1 and cfg.dec_skip_last_residual()
            var_x = self._upscale_block(var_x, filts, skip_residual=skip_res)
            if cfg_loss.learn_mask():
                var_y = self._upscale_block(var_y, filts, is_mask=True)
        retval = [var_x, var_y] if cfg_loss.learn_mask() else var_x
        return retval