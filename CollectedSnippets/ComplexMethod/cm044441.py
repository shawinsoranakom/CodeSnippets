def _mssism(self,  # pylint:disable=too-many-locals
                y_true: torch.Tensor,
                y_pred: torch.Tensor,
                filter_size: int) -> torch.Tensor:
        """Perform the MSSISM calculation.

        Ported from Tensorflow implementation `image.ssim_multiscale`

        Parameters
        ----------
        y_true
            The ground truth value
        y_pred
            The predicted value
        filter_size
            The filter size to use
        """
        images = [y_true, y_pred]
        shapes = [y_true.shape, y_pred.shape]
        heads = [s[:-3] for s in shapes]
        tails = [s[-3:] for s in shapes]

        mcs = []
        ssim_per_channel = None
        for k in range(len(self._power_factors)):
            if k > 0:
                # Avg pool takes rank 4 tensors. Flatten leading dimensions.
                flat_images = [(x.reshape(-1, *t)) for x, t in zip(images, tails)]
                remainder = torch.tensor(list(tails[0]),
                                         dtype=torch.int32,
                                         device=y_pred.device) % self._divisor_tensor
                if (remainder != 0).any():
                    flat_images = self._do_pad(flat_images, remainder)

                downscaled = [F.avg_pool2d(x,  # pylint:disable=not-callable
                                           self._divisor[1:3],
                                           stride=self._divisor[1:3],
                                           padding=0)
                              for x in flat_images]

                tails = [x.shape[1:] for x in downscaled]
                images = [x.reshape(*h, *t) for x, h, t in zip(downscaled, heads, tails)]

            # Overwrite previous ssim value since we only need the last one.
            ssim_per_channel, cs_ = self._ssim_per_channel(images[0], images[1], filter_size)
            mcs.append(F.relu(cs_))

        mcs.pop()  # Remove the cs score for the last scale.
        assert ssim_per_channel is not None
        mcs_and_ssim = torch.stack(mcs + [F.relu(ssim_per_channel)], dim=-1)
        ms_ssim = torch.prod(mcs_and_ssim ** self._power_factors, dim=-1)
        return ms_ssim.mean(dim=-1)