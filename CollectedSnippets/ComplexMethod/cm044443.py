def forward(self, y_true: torch.Tensor, y_pred: torch.Tensor
                ) -> torch.Tensor | tuple[torch.Tensor, list[torch.Tensor]]:
        """Perform the LPIPS Loss Function.

        Parameters
        ----------
        y_true
            The ground truth batch of images
        y_pred
            The predicted batch of images

        Returns
        -------
        The final loss value for each item in the batch
        """
        if not self._initialized:
            self._shift = self._shift.to(y_pred.device)
            self._scale = self._scale.to(y_pred.device)
            self._trunk_net = self._trunk_net.to(y_pred.device)
            self._linear_net = self._linear_net.to(y_pred.device)
            self._initialized = True

        if not self._is_rgb:
            y_true = torch.flip(y_true, dims=[-1])
            y_pred = torch.flip(y_pred, dims=[-1])
        y_true = y_true.permute(0, 3, 1, 2)
        y_pred = y_pred.permute(0, 3, 1, 2)

        if self._normalize:
            y_true = (y_true * 2.0) - 1.0
            y_pred = (y_pred * 2.0) - 1.0

        y_true = (y_true - self._shift) / self._scale
        y_pred = (y_pred - self._shift) / self._scale

        net_true = self._trunk_net(y_true)
        net_pred = self._trunk_net(y_pred)

        diffs = [(out_true - out_pred) ** 2
                 for out_true, out_pred in zip(net_true, net_pred)]

        dims = y_true.shape[2:4]
        if self._crop_amount:
            diffs = [d[:, :, i:-i, i: -i] if i else d
                     for d, i in zip(diffs, self._crop_amount)]

        dims = dims if self._spatial else y_true.shape[2:4]
        res = [self._process_output(diff, dims) for diff in self._process_diffs(diffs)]

        if self._spatial:
            val = torch.stack(res, dim=0).sum(dim=0)
        else:
            val = torch.stack([r.sum(dim=(1, 2, 3)) for r in res]).sum(dim=0)

        val *= 0.1  # Reduce by factor of 10 'cos this loss is STRONG. # TODO config

        retval = (val, res) if self._ret_per_layer else val
        return retval