def _reduce_data(
        self,
        batch: list[NestedTensors],
        *,
        pin_memory: bool,
    ) -> NestedTensors:
        if len(batch) > 0 and is_list_of(batch, torch.Tensor, check="all"):
            batch = cast(list[torch.Tensor], batch)
            if len(batch) == 1:
                # An optimization when `batch` contains only one tensor:
                # - produce exactly same result as `torch.concat(batch)`
                # - will achieve zero-copy if the tensor is contiguous
                return batch[0].contiguous()

            dim = self.dim + (self.dim < 0) * len(batch[0].shape)

            def _shape_before_after(tensor: torch.Tensor):
                return tensor.shape[:dim], tensor.shape[dim + 1 :]

            first_shape = _shape_before_after(batch[0])

            if all(_shape_before_after(elem) == first_shape for elem in batch):
                shape_before, shape_after = first_shape
                shape_concat = sum(item.shape[dim] for item in batch)
                out = torch.empty(
                    (*shape_before, shape_concat, *shape_after),
                    dtype=batch[0].dtype,
                    device=batch[0].device,
                    pin_memory=pin_memory,
                )
                return torch.concat(batch, dim=self.dim, out=out)

            # Variable-length case: non-concat dimensions differ
            # (e.g., Ultravox with different audio durations).
            # Use slice-assign approach (more efficient than padding).
            # See: https://github.com/vllm-project/vllm/issues/31658

            ndim = batch[0].ndim

            # Step 1: Compute output shape
            # - Non-concat dims: take max across batch
            # - Concat dim: sum across batch
            max_sizes: list[int] = []
            for d in range(ndim):
                if d == dim:
                    max_sizes.append(sum(t.shape[d] for t in batch))
                else:
                    max_sizes.append(max(t.shape[d] for t in batch))

            # Step 2: Create zero-initialized output tensor
            out = torch.zeros(
                max_sizes,
                dtype=batch[0].dtype,
                device=batch[0].device,
                pin_memory=pin_memory,
            )

            # Step 3: Slice-assign each tensor to its proper position
            concat_offset = 0
            for tensor in batch:
                slices: list[slice] = []
                for d in range(ndim):
                    if d == dim:
                        slices.append(
                            slice(concat_offset, concat_offset + tensor.shape[d])
                        )
                    else:
                        slices.append(slice(0, tensor.shape[d]))
                out[tuple(slices)] = tensor
                concat_offset += tensor.shape[dim]

            return out

        assert self.dim == 0, "dim == 0 is required for nested list"
        return [e for elem in batch for e in elem]