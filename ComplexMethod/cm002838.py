def forward(ctx, time_decay, time_first, key, value, state=None, return_state=False):
        batch_size, seq_len, hidden_size = key.size()
        if seq_len > rwkv_cuda_kernel.max_seq_length:
            raise ValueError(
                f"Cannot process a batch with {seq_len} tokens at the same time, use a maximum of "
                f"{rwkv_cuda_kernel.max_seq_length} with this model."
            )
        if batch_size * hidden_size % min(hidden_size, 32) != 0:
            raise ValueError(
                f"The product of batch size ({batch_size}) and hidden size ({hidden_size}) needs to be a round "
                f"multiple of {min(hidden_size, 32)}."
            )

        ctx.input_dtype = key.dtype

        if (
            time_decay.device.type != "cuda"
            or time_first.device.type != "cuda"
            or key.device.type != "cuda"
            or value.device.type != "cuda"
        ):
            raise ValueError("Calling the CUDA kernel for wkv attention requires all tensors to be on CUDA devices.")

        time_decay = -torch.exp(time_decay.float().contiguous())
        if key.dtype == torch.float16:
            time_first = time_first.float()
            key = key.float()
            value = value.float()
        time_first = time_first.contiguous()
        key = key.contiguous()
        value = value.contiguous()
        # The CUDA kernel will fill this tensor.
        output = torch.empty_like(key, memory_format=torch.contiguous_format)
        if return_state or state is not None:
            if state is None:
                state = torch.zeros(
                    batch_size,
                    hidden_size,
                    3,
                    dtype=torch.float32,
                    device=key.device,
                    memory_format=torch.contiguous_format,
                )
                state[:, :, 2] -= 1e38
            else:
                state = torch.cat([s.unsqueeze(2) for s in state], dim=2).contiguous()
            if key.dtype == torch.bfloat16:
                forward_func = rwkv_cuda_kernel.forward_with_state_bf16
            else:
                forward_func = rwkv_cuda_kernel.forward_with_state
            forward_func(time_decay, time_first, key, value, output, state)
        else:
            forward_func = rwkv_cuda_kernel.forward_bf16 if key.dtype == torch.bfloat16 else rwkv_cuda_kernel.forward
            forward_func(time_decay, time_first, key, value, output)

        ctx.save_for_backward(time_decay, time_first, key, value, output)

        if state is not None:
            state = [s.squeeze(2) for s in torch.chunk(state, 3, dim=2)]

        return output.to(ctx.input_dtype), state