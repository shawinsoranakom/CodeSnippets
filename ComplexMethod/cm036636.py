def test_roundtrip_non_contiguous_tensors(self):
        """Test roundtrip with non-contiguous tensors from the trainer."""
        # Create non-contiguous tensors (simulating trainer outputs)
        # Transposed tensors are non-contiguous
        weight1 = torch.randn(20, 10, dtype=torch.float32).cuda().T
        # Sliced tensors with step are non-contiguous
        weight2 = torch.randn(40, 30, dtype=torch.float16).cuda()[::2, ::2]
        # Permuted tensors are non-contiguous
        weight3 = torch.randn(5, 10, 15, dtype=torch.bfloat16).cuda().permute(2, 0, 1)

        params = [
            ("layer1.weight", weight1),
            ("layer2.weight", weight2),
            ("layer3.weight", weight3),
        ]

        # Verify tensors are indeed non-contiguous
        for name, tensor in params:
            assert not tensor.is_contiguous(), f"{name} should be non-contiguous"

        buffer_size = 500
        producer_group = MockCommunicationGroup()

        packed_broadcast_producer(
            iterator=iter(params),
            group=producer_group,
            src=0,
            post_iter_func=lambda x: x[1],
            buffer_size_bytes=buffer_size,
        )

        consumer_group = MockConsumerCommunicationGroup(
            producer_group.broadcasted_tensors
        )

        state_dict_info = create_state_dict_info(params)
        unpacked_tensors = {}

        def post_unpack_func(tensor_list):
            for name, tensor in tensor_list:
                unpacked_tensors[name] = tensor.clone()

        packed_broadcast_consumer(
            iterator=iter(state_dict_info.items()),
            group=consumer_group,
            src=0,
            post_unpack_func=post_unpack_func,
            buffer_size_bytes=buffer_size,
        )

        # Verify all non-contiguous params roundtrip correctly
        for name, original_tensor in params:
            assert name in unpacked_tensors
            unpacked = unpacked_tensors[name]
            assert unpacked.shape == original_tensor.shape
            assert unpacked.dtype == original_tensor.dtype
            assert torch.allclose(unpacked, original_tensor, rtol=1e-4, atol=1e-6)