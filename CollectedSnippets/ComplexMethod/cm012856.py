def forward(self, x_orig: torch.Tensor) -> torch.Tensor:  # pyre-ignore[14]
        if x_orig.numel() == 0:
            return x_orig
        x = x_orig.detach()
        x_min, x_max = torch.aminmax(x)
        # want to ignore torch.inf since we don't actually
        # want to make our quantization range infinite
        # and in practice those values will be clamped
        if x_min == -torch.inf or x_max == torch.inf:
            warnings.warn(
                "torch.inf detected in input tensor, ignoring input", stacklevel=2
            )
            x = x[x.abs() != torch.inf]
            if x.numel() == 0:
                return x_orig
            x_min, x_max = torch.aminmax(x)

        current_min = self.min_val
        current_max = self.max_val

        is_uninitialized = self.min_val == float("inf") or self.max_val == float("-inf")
        if is_uninitialized:
            self.reset_histogram(x, x_min, x_max)
        else:
            update_min, update_max = x_min, x_max
            new_min = torch.min(current_min, update_min)
            new_max = torch.max(current_max, update_max)

            # TODO: For some reason, this is required for it to pass torchscript test
            # new_min and new_max should already have requires_grad set to False
            new_min, new_max = new_min.detach(), new_max.detach()
            update_histogram = torch.histc(
                x,
                self.bins,
                min=new_min,  # type: ignore[arg-type]
                max=new_max,  # type: ignore[arg-type]
            ).to(self.histogram.device)
            if new_min == current_min and new_max == current_max:
                combined_histogram = self.histogram + update_histogram
                self.histogram.detach_().resize_(combined_histogram.shape)
                self.histogram.copy_(combined_histogram)
            else:
                combined_histogram = self._combine_histograms(
                    self.histogram,
                    current_min,
                    current_max,
                    update_histogram,
                    new_min,
                    new_max,
                )
                self.histogram.detach_().resize_(combined_histogram.shape)
                self.histogram.copy_(combined_histogram)
                self.min_val.detach_().resize_(new_min.shape)
                self.min_val.copy_(new_min)
                self.max_val.detach_().resize_(new_max.shape)
                self.max_val.copy_(new_max)

        return x_orig