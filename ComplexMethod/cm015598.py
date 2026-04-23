def test_split_tensor_1D(self) -> None:
        mesh = self.build_device_mesh()
        shard_placement = Shard(0)

        for size in range(8):
            tensor = self._create_tensor(size)
            splitted_tensor_list, pad_sizes = shard_placement._split_tensor(
                tensor,
                mesh.size(),
                with_padding=True,
                contiguous=True,
            )
            if size == 0:
                # when tensor size is 0, there is no padding needed for all the ranks.
                expected_pad_sizes = [0] * self.world_size
                assert_array_equal(expected_pad_sizes, pad_sizes)

                is_tensor_empty = [
                    not splitted_tensor.numel() > 0
                    for splitted_tensor in splitted_tensor_list
                ]
                expected_is_tensor_empty = [True] * self.world_size
                assert_array_equal(expected_is_tensor_empty, is_tensor_empty)
            else:
                expected_pad_sizes = [
                    0 if idx < size else 1
                    for idx, _ in enumerate(range(self.world_size))
                ]
                assert_array_equal(expected_pad_sizes, pad_sizes)

                from torch.distributed.tensor._collective_utils import unpad_tensor

                unpadded_list = [
                    (
                        unpad_tensor(tensor, shard_placement.dim, pad_sizes[i])
                        if pad_sizes[i] > 0
                        else tensor
                    )
                    for i, tensor in enumerate(splitted_tensor_list)
                ]
                expected_is_tensor_empty = [
                    not idx < size for idx, _ in enumerate(range(self.world_size))
                ]
                is_tensor_empty = [
                    not unpadded_tensor.numel() > 0 for unpadded_tensor in unpadded_list
                ]
                assert_array_equal(expected_is_tensor_empty, is_tensor_empty)