def test_consumer_receives_tensors(self):
        """Test that consumer receives and unpacks tensors."""
        params = create_mock_model_params()
        params_cuda = [(name, tensor.cuda()) for name, tensor in params]

        buffer_size = 2000

        # First, run producer to get the broadcasted tensors
        producer_group = MockCommunicationGroup()

        packed_broadcast_producer(
            iterator=iter(params_cuda),
            group=producer_group,
            src=0,
            post_iter_func=lambda x: x[1],
            buffer_size_bytes=buffer_size,
        )

        # Now run consumer with the broadcasted tensors
        consumer_group = MockConsumerCommunicationGroup(
            producer_group.broadcasted_tensors
        )

        state_dict_info = create_state_dict_info(params_cuda)

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

        # Verify all parameters were unpacked
        assert len(unpacked_tensors) == len(params)

        # Verify each tensor matches the original
        for name, original_tensor in params_cuda:
            assert name in unpacked_tensors
            unpacked = unpacked_tensors[name]
            assert unpacked.shape == original_tensor.shape
            assert unpacked.dtype == original_tensor.dtype
            assert torch.allclose(unpacked, original_tensor, rtol=1e-5, atol=1e-7)