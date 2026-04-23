def flatten_tensors(
        self,
        tensors: list[Tensor],
        aligned_numel: int,
    ) -> Tensor:
        """
        Flatten ``tensors`` into a single flat tensor.

        The flattening optionally includes
        padding if ``aligned_numel`` is greater than 0, where ``aligned_numel``
        gives the numel required to have address alignment.

        NOTE: The padding alignment algorithm must be kept in sync with
        :meth:`_init_flat_param_metadata`. We separate the two methods because
        the initialization happens once, whereas this method may be called
        multiple times throughout training (e.g. for checkpointing).
        """
        if len(tensors) == 0:
            raise ValueError("Expects non-empty `tensors`")
        if aligned_numel < 0:
            raise ValueError(
                f"Expects non-negative `aligned_numel` but got {aligned_numel}"
            )
        dtype, _, device = self._validate_tensors_to_flatten(tensors)
        flat_tensors: list[Tensor] = []
        if aligned_numel > 0:
            total_numel = 0
            for tensor in tensors:
                numel_to_pad = aligned_numel - (total_numel % aligned_numel)
                if numel_to_pad > 0 and numel_to_pad < aligned_numel:
                    padding_tensor = _construct_padding_tensor(
                        numel_to_pad, dtype, False, device
                    )
                    flat_tensors.append(padding_tensor)
                    total_numel += numel_to_pad
                flat_tensors.append(
                    torch.flatten(_detach_if_needed(tensor))
                    if _is_truly_contiguous(tensor)
                    else _detach_if_needed(tensor).as_strided((tensor.numel(),), (1,))
                )
                total_numel += tensor.numel()
            numel_to_pad = self.world_size - (total_numel % self.world_size)
            if numel_to_pad > 0 and numel_to_pad < self.world_size:
                padding_tensor = _construct_padding_tensor(
                    numel_to_pad, dtype, False, device
                )
                flat_tensors.append(padding_tensor)
                total_numel += numel_to_pad
        else:
            flat_tensors = [
                torch.flatten(_detach_if_needed(tensor))
                if _is_truly_contiguous(tensor)
                else _detach_if_needed(tensor).as_strided((tensor.numel(),), (1,))
                for tensor in tensors
            ]
        return torch.cat(flat_tensors, dim=0)