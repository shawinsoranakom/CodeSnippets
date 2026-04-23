def wrap_chunkwise_arbitrary_sequence_length(
        mlstm_chunkwise_kernel: Callable,
        mlstm_sequence_kernel: Callable,
        mlstm_step_kernel: Callable,
        query: torch.Tensor,
        key: torch.Tensor,
        value: torch.Tensor,
        fgate: torch.Tensor,
        igate: torch.Tensor,
        c_initial: torch.Tensor | None = None,
        n_initial: torch.Tensor | None = None,
        m_initial: torch.Tensor | None = None,
        return_last_states: bool = True,
        eps: float = 1e-6,
        autocast_kernel_dtype: torch.dtype = torch.bfloat16,
        chunk_size: int = 64,
        enable_logging: bool = False,
    ) -> torch.Tensor | tuple[torch.Tensor, tuple[torch.Tensor, torch.Tensor, torch.Tensor]]:
        """This function computes the last hidden state and matH outputs of the mLSTM, independently of the sequence length.

        For this it uses three kernels:
        - mlstm_chunkwise_kernel: mlstm chunkwise kernels that processes chunks of a given chunk size in parallel.
        - mlstm_sequence_kernel: mlstm kernel that processes the remaining sequence length in a single step recurrence.
        - mlstm_step_kernel: mlstm kernel that processes a sequence length of 1 in a single step.

        It tries to maximize the chunksizes to improve performance.
        It will start with the given chunk size and then divides the chunksize by 2 until the chunk size is smaller than 16.
        At every chunksize it will process the maximal number of chunks that fit into the remaining sequence length.

        E.g. for chunk_size = 64, this function will try the chunksizes [64, 32, 16] if necessary.

        For the remaining sequence length, which is smaller than 16, we use a different kernel that computes the mLSTM
        in a single step and loop over this in pytorch.

        Args:
            mlstm_chunkwise_kernel: The mLSTM chunkwise kernel that processes chunks of a given chunk size in parallel
            mlstm_sequence_kernel: The mLSTM kernel that processes the remaining sequence length in a single step recurrence
            query: The query tensor (batch_size, nh, sequence_length, dhqk)
            key: The key tensor (batch_size, nh, sequence_length, dhqk)
            value: The value tensor (batch_size, nh, sequence_length, dhhv)
            fgate: The forget gate tensor (batch_size, nh, sequence_length)
            igate: The input gate tensor (batch_size, nh, sequence_length)
            c_initial: The initial cell state tensor (batch_size, nh, dhqk, dhhv)
            n_initial: The initial hidden state tensor (batch_size, nh, dhqk)
            m_initial: The initial memory state tensor (batch_size, nh, 1)
            return_last_states: If True, the function will return the last states of the mLSTM
            eps: The epsilon value used for numerical stability
            autocast_kernel_dtype: The dtype used for the kernel computation
            chunk_size: The chunk size used for the chunkwise kernel
            enable_logging: If True, the function will log debug information. Default is False.

        Returns:
            The last hidden state tensor (batch_size, nh, sequence_length, dhhv) or a tuple containing the last hidden state tensor and the last states of the mLSTM
            Last states are (cstate (batch_size, nh, dhqk, dhhv), nstate (batch_size, nh, dhqk), mstate (batch_size, nh, 1)).
        """

        batch_size, nh, sequence_length, dhqk = key.shape
        dhhv = value.shape[-1]

        c_state = (
            c_initial
            if c_initial is not None
            else torch.zeros(batch_size, nh, dhqk, dhhv, device=key.device, dtype=torch.float32)
        )
        n_state = (
            n_initial
            if n_initial is not None
            else torch.zeros(batch_size, nh, dhqk, device=key.device, dtype=torch.float32)
        )
        m_state = (
            m_initial
            if m_initial is not None
            else torch.zeros(batch_size, nh, 1, device=key.device, dtype=torch.float32)
        )

        if sequence_length > 1:
            # process the sequence length in chunks
            h_outs = []
            seq_len_start_idx = 0
            remaining_seq_len = sequence_length - seq_len_start_idx
            num_chunks = remaining_seq_len // chunk_size
            if num_chunks > 0:
                iter_seq_len = chunk_size * num_chunks
                seq_len_idx = seq_len_start_idx + iter_seq_len
                h_out, (c_state, n_state, m_state) = mlstm_chunkwise_kernel(
                    query=query[..., seq_len_start_idx:seq_len_idx, :].contiguous(),
                    key=key[..., seq_len_start_idx:seq_len_idx, :].contiguous(),
                    value=value[..., seq_len_start_idx:seq_len_idx, :].contiguous(),
                    fgate=fgate[..., seq_len_start_idx:seq_len_idx].contiguous(),
                    igate=igate[..., seq_len_start_idx:seq_len_idx].contiguous(),
                    c_initial=c_state,
                    n_initial=n_state,
                    m_initial=m_state,
                    chunk_size=chunk_size,
                    return_last_states=True,
                    autocast_kernel_dtype=autocast_kernel_dtype,
                    eps=eps,
                )
                seq_len_start_idx += iter_seq_len
                h_outs.append(h_out)

            remaining_seq_len = sequence_length - seq_len_start_idx

            if remaining_seq_len > 0:
                # we use here matK as query as this kernel does not need a query, since we do not care about the outputs only about the last state
                h_out, (c_state, n_state, m_state) = mlstm_sequence_kernel(
                    query=query[..., seq_len_start_idx:sequence_length, :].contiguous(),
                    key=key[..., seq_len_start_idx:sequence_length, :].contiguous(),
                    value=value[..., seq_len_start_idx:sequence_length, :].contiguous(),
                    igate=igate[..., seq_len_start_idx:sequence_length].contiguous(),
                    fgate=fgate[..., seq_len_start_idx:sequence_length].contiguous(),
                    c_initial=c_state,
                    n_initial=n_state,
                    m_initial=m_state,
                    return_last_states=True,
                    eps=eps,
                )
                h_outs.append(h_out)
            h_out = torch.concatenate(h_outs, dim=2)

        else:
            if sequence_length != 1:
                raise ValueError(
                    f"Received empty sequence (sequence_length={sequence_length}), require at least single element in the sequence."
                )
            # process the sequence length in a single step
            # while this case is also captured by the regular mode above,
            # it avoids the overhead of the loop and calls the step kernel directly
            # The step function does not want a sequence dimension
            # qkv shape is (batch_size, nh, dhqk/dhv)
            # igate, fgate shape is (batch_size, nh, 1)
            h_out, (c_state, n_state, m_state) = mlstm_step_kernel(
                query=query.squeeze(2),
                key=key.squeeze(2),
                value=value.squeeze(2),
                igate=igate,
                fgate=fgate,
                cstate=c_state,
                nstate=n_state,
                mstate=m_state,
                eps=eps,
            )
            h_out = h_out[:, :, None, :]

        if return_last_states:
            return h_out, (c_state, n_state, m_state)
        else:
            return h_out