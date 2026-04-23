def _update_values(self, t: _TensorMetadata | None) -> None:
        key = TensorKey.from_tensor(t)
        if key is not None and t is not None and t.layout == torch.strided:
            # Scalars are represented as zero dim Tensors
            n = max(
                i[0] * i[1] for i in zip(t.sizes or [1], t.strides or [1], strict=True)
            )

            num_bytes = n * _element_size(t.dtype)
            if num_bytes < 0:
                raise AssertionError(f"num_bytes must be non-negative, got {num_bytes}")
            self._values[key] = max(self._values.get(key, 0), num_bytes)