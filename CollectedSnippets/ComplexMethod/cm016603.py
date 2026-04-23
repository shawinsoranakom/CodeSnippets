def _move_adapter_weights_to_device(self, device, dtype=None):
        """Move adapter weights to specified device to avoid per-forward transfers.

        Handles both:
            - WeightAdapterBase: has self.weights tuple of tensors
            - WeightAdapterTrainBase: nn.Module with parameters, uses .to() method
        """
        adapter = self.adapter

        # Check if adapter is an nn.Module (WeightAdapterTrainBase)
        if isinstance(adapter, nn.Module):
            # In training mode we don't touch dtype as trainer will handle it
            adapter.to(device=device)
            logging.debug(
                f"[BypassHook] Moved training adapter (nn.Module) to {device}"
            )
            return

        # WeightAdapterBase: handle self.weights tuple
        if not hasattr(adapter, "weights") or adapter.weights is None:
            return

        weights = adapter.weights
        if isinstance(weights, (list, tuple)):
            new_weights = []
            for w in weights:
                if isinstance(w, torch.Tensor):
                    if dtype is not None:
                        new_weights.append(w.to(device=device, dtype=dtype))
                    else:
                        new_weights.append(w.to(device=device))
                else:
                    new_weights.append(w)
            adapter.weights = (
                tuple(new_weights) if isinstance(weights, tuple) else new_weights
            )
        elif isinstance(weights, torch.Tensor):
            if dtype is not None:
                adapter.weights = weights.to(device=device, dtype=dtype)
            else:
                adapter.weights = weights.to(device=device)

        logging.debug(f"[BypassHook] Moved adapter weights to {device}")