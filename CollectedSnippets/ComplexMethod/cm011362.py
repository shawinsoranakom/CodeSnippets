def _read_quantized_tensor_with_block_alignment(
        self, req: ReadItem, safetensor_file: Any
    ) -> torch.Tensor:
        """
        Read a quantized tensor with block alignment.

        Args:
            req: Read request containing tensor info and required slices
            safetensor_file: Open safetensors file handle

        Returns:
            Dequantized tensor ready for use
        """
        tensor_fqn = req.storage_index.fqn
        scale_fqn = self._weight_scale_mapping[tensor_fqn]

        try:
            group_start = 0
            offset_in_first_group = 0
            if tensor_fqn.endswith("_blocks"):
                # Full tensor is a 4D MXFP4 quantized tensor: [..., G, B].
                # Each group G produces B * 2 dequantized values.
                # Checkpoint [..., G, B] -> dequantized [..., G*B*2].

                # The planner gives 3D requests based on the dequantized shape.
                # Need to figure out which groups (dimension 2 in checkpoint) to read.

                # Use the quantized checkpoint shape to get the correct B.
                *prefix_shape, B = self._tensor_full_shapes[tensor_fqn + "_quantized"]
                values_per_group = B * 2  # Each byte has 2 nibbles (4-bit values).

                # Calculate which groups we need based on the requested range in dim 2.
                # Ensure the reequest is in 3D.
                if len(req.storage_offsets) != 3:
                    raise AssertionError

                # Positions in dequantized space.
                dim2_start_deq = req.storage_offsets[2]
                dim2_length_deq = req.lengths[2]
                dim2_end_deq = dim2_start_deq + dim2_length_deq

                # Convert to group indices.
                group_start = dim2_start_deq // values_per_group
                group_end = (dim2_end_deq + values_per_group - 1) // values_per_group

                # Read only the necessary groups from checkpoint.
                weight_slices_4d = (
                    slice(
                        req.storage_offsets[0], req.storage_offsets[0] + req.lengths[0]
                    ),
                    slice(
                        req.storage_offsets[1], req.storage_offsets[1] + req.lengths[1]
                    ),
                    slice(group_start, group_end),
                    slice(None),  # Read all B values for each group.
                )
                quantized_tensor = safetensor_file.get_slice(tensor_fqn)[
                    weight_slices_4d
                ]

                # Also track the offset within the first group
                offset_in_first_group = dim2_start_deq - (
                    group_start * values_per_group
                )
            else:
                # 2D quantized tensor, use 2d block partition.
                weight_slices = tuple(
                    slice(offset, offset + length)
                    for offset, length in zip(req.storage_offsets, req.lengths)
                )
                quantized_tensor = safetensor_file.get_slice(tensor_fqn)[weight_slices]

            # Load the corresponding scale inverse tensor (full tensor)
            scale_file_name = self._weight_map.get(scale_fqn)
            if scale_file_name is None:
                raise ValueError(f"Scale tensor {scale_fqn} not found in weight_map")

            # Check if scale tensor is in the same file as the weight tensor
            weight_file_name = self._weight_map.get(tensor_fqn)

            if scale_file_name == weight_file_name:
                # Scale tensor is in the same file, use current handle
                scale_inv = safetensor_file.get_tensor(scale_fqn)
            else:
                # Scale tensor is in a different file, need to open it
                from safetensors import safe_open  # type: ignore[import]

                scale_file_path = Path(self.path) / scale_file_name
                with safe_open(
                    scale_file_path, framework="pt", device="cpu"
                ) as scale_file:
                    scale_inv = scale_file.get_tensor(scale_fqn)

            # Get the full tensor shape from our O(1) lookup cache
            full_tensor_shape = self._tensor_full_shapes.get(tensor_fqn)
            if full_tensor_shape is None:
                raise ValueError(f"Could not find full tensor shape for {tensor_fqn}")

            # Determine which dequantization function to use.
            if len(full_tensor_shape) == 2:
                # 2D block-wise quantization, e.g., used in deepseek v3.1
                slice_info = self._get_slice_to_block_mapping(req)
                dequantized_tensor = self._dequantize_tensor(
                    weight=quantized_tensor,
                    scale_inv=scale_inv,
                    full_tensor_shape=full_tensor_shape,
                    slice_info=slice_info,
                )
            elif tensor_fqn.endswith("_blocks"):
                # 4D with blocks along dimension 2, used in MXFP4, e.g. gpt-oss
                dequantized_tensor = self._dequantize_tensor_mxfp4(
                    blocks=quantized_tensor,
                    scales=scale_inv,
                    req=req,
                    group_start=group_start,
                    offset_in_first_group=offset_in_first_group,
                )
            else:
                raise ValueError("Unsupported quantization types")

            return dequantized_tensor

        except Exception as e:
            logger.error("Failed to read the quantized tensor!!")
            raise e