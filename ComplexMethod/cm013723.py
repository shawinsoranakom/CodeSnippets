def backward(self, grad_output):
        if not (
            grad_output.is_contiguous(memory_format=torch.channels_last)
            or grad_output.is_contiguous(memory_format=torch.channels_last_3d)
        ):
            grad_output = grad_output.contiguous()
        saved_input, weight, mean, invstd, count_tensor = self.saved_tensors
        grad_input = grad_weight = grad_bias = None
        process_group = self.process_group

        if saved_input.numel() > 0:
            # calculate local stats as well as grad_weight / grad_bias
            (
                sum_dy,
                sum_dy_xmu,
                grad_weight,
                grad_bias,
            ) = torch.batch_norm_backward_reduce(
                grad_output,
                saved_input,
                mean,
                invstd,
                weight,
                self.needs_input_grad[0],
                self.needs_input_grad[1],
                self.needs_input_grad[2],
            )

            if self.needs_input_grad[0]:
                # synchronizing stats used to calculate input gradient.
                num_channels = sum_dy.shape[0]
                combined = torch.cat([sum_dy, sum_dy_xmu], dim=0)
                torch.distributed.all_reduce(
                    combined,
                    torch.distributed.ReduceOp.SUM,
                    process_group,
                    async_op=False,
                )
                sum_dy, sum_dy_xmu = torch.split(combined, num_channels)

                # backward pass for gradient calculation
                if weight is not None and weight.dtype != mean.dtype:
                    weight = weight.to(mean.dtype)
                grad_input = torch.batch_norm_backward_elemt(
                    grad_output,
                    saved_input,
                    mean,
                    invstd,
                    weight,
                    sum_dy,
                    sum_dy_xmu,
                    count_tensor,
                )
            # synchronizing of grad_weight / grad_bias is not needed as distributed
            # training would handle all reduce.
            if weight is None or not self.needs_input_grad[1]:
                grad_weight = None

            if weight is None or not self.needs_input_grad[2]:
                grad_bias = None
        else:
            # This process got an empty input tensor in the forward pass.
            # Although this process can directly set grad_input as an empty
            # tensor of zeros, it still needs to participate in the collective
            # communication to unblock its peers, as other peer processes might
            # have received non-empty inputs.
            num_channels = saved_input.shape[1]
            if self.needs_input_grad[0]:
                # launch all_reduce to unblock other peer processes
                combined = torch.zeros(
                    2 * num_channels, dtype=saved_input.dtype, device=saved_input.device
                )
                torch.distributed.all_reduce(
                    combined,
                    torch.distributed.ReduceOp.SUM,
                    process_group,
                    async_op=False,
                )

            # Leave grad_input, grad_weight and grad_bias as None, which will be
            # interpreted by the autograd engine as Tensors full of zeros.

        return grad_input, grad_weight, grad_bias, None, None, None, None, None, None