def forward(self, input: Tensor) -> Tensor:
        """
        Runs the forward pass.
        """
        self._check_input_dim(input)
        self._check_non_zero_input_channels(input)

        # exponential_average_factor is set to self.momentum
        # (when it is available) only so that it gets updated
        # in ONNX graph when this node is exported to ONNX.
        if self.momentum is None:
            exponential_average_factor = 0.0
        else:
            exponential_average_factor = self.momentum

        if self.training and self.track_running_stats:
            if self.num_batches_tracked is None:
                raise AssertionError("num_batches_tracked must not be None")
            self.num_batches_tracked.add_(1)
            if self.momentum is None:  # use cumulative moving average
                exponential_average_factor = 1.0 / self.num_batches_tracked.item()
            else:  # use exponential moving average
                exponential_average_factor = self.momentum

        r"""
        Decide whether the mini-batch stats should be used for normalization rather than the buffers.
        Mini-batch stats are used in training mode, and in eval mode when buffers are None.
        """
        if self.training:
            bn_training = True
        else:
            bn_training = (self.running_mean is None) and (self.running_var is None)

        r"""
        Buffers are only updated if they are to be tracked and we are in training mode. Thus they only need to be
        passed when the update should occur (i.e. in training mode when they are tracked), or when buffer stats are
        used for normalization (i.e. in eval mode when buffers are not None).
        """
        # If buffers are not to be tracked, ensure that they won't be updated
        running_mean = (
            self.running_mean if not self.training or self.track_running_stats else None
        )
        running_var = (
            self.running_var if not self.training or self.track_running_stats else None
        )

        # Don't sync batchnorm stats in inference mode (model.eval()).
        need_sync = (
            bn_training
            and self.training
            and torch.distributed.is_available()
            and torch.distributed.is_initialized()
        )
        if need_sync:
            # currently only GPU/PrivateUse1 input is supported
            if input.device.type not in [
                "cuda",
                "hpu",
                "xpu",
                torch._C._get_privateuse1_backend_name(),
            ]:
                raise ValueError(
                    "SyncBatchNorm expected input tensor to be on GPU or XPU or "
                    f"{torch._C._get_privateuse1_backend_name()}"
                )

            process_group = torch.distributed.group.WORLD
            if self.process_group:
                process_group = self.process_group
            world_size = torch.distributed.get_world_size(process_group)
            need_sync = world_size > 1

        # fallback to framework BN when synchronization is not necessary
        if not need_sync:
            return F.batch_norm(
                input,
                running_mean,
                running_var,
                self.weight,
                self.bias,
                bn_training,
                exponential_average_factor,
                self.eps,
            )
        else:
            if not bn_training:
                raise AssertionError("bn_training must be True")
            return sync_batch_norm.apply(
                input,
                self.weight,
                self.bias,
                running_mean,
                running_var,
                self.eps,
                exponential_average_factor,
                process_group,  # type: ignore[possibly-undefined]
                world_size,  # type: ignore[possibly-undefined]
            )