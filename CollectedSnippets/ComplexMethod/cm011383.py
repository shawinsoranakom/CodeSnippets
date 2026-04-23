def decompress(fut):
        state.q_memory_dict[bucket_index] = fut.value().div_(world_size)

        for p, q, tensor in zip(ps, qs, tensors_to_compress):
            torch.bmm(p, q.transpose(1, 2), out=tensor)

        # Copy batched tensors back to original buffer.
        if state.batch_tensors_with_same_shape:
            for tensor in tensors_to_compress:
                if tensor.shape[0] == 1:
                    # Skip tensor with batch_size == 1 since itself is the original tensor.
                    continue
                original_tensors = shape_to_tensors[tensor.shape[1:]]
                for i, original_tensor in enumerate(original_tensors):
                    original_tensor.copy_(tensor[i])

        if torch.cuda.is_available():
            torch.cuda.synchronize(device)

        if state.use_error_feedback:
            # Memorize the local errors.
            if input_tensor_cp is None:
                raise AssertionError
            state.error_dict[bucket_index] = input_tensor_cp - input_tensor
        if not state.warm_start:
            state.p_memory_dict.clear()
            state.q_memory_dict.clear()

        state.maybe_increase_iter(bucket)

        return input_tensor