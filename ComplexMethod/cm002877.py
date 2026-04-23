def mlstm_recurrent_sequence_native(
        query: torch.Tensor,
        key: torch.Tensor,
        value: torch.Tensor,
        igate: torch.Tensor,
        fgate: torch.Tensor,
        c_initial: torch.Tensor | None = None,
        n_initial: torch.Tensor | None = None,
        m_initial: torch.Tensor | None = None,
        return_last_states: bool = False,
        eps: float = 1e-6,
        dtype_state: torch.dtype = torch.float32,
        **kwargs,
    ) -> tuple[
        torch.Tensor,
        torch.Tensor,
        torch.Tensor,
        tuple[torch.Tensor, torch.Tensor, torch.Tensor] | None,
        tuple[torch.Tensor, torch.Tensor, torch.Tensor] | None,
    ]:
        batch_size, nh, sequence_length, dhqk = query.shape
        dhv = value.shape[-1]
        device = query.device

        if c_initial is not None:
            if n_initial is None or m_initial is None:
                raise ValueError("Initial states must be provided together.")
            if n_initial is None or m_initial is None:
                raise ValueError("Initial states must be provided together.")
            matC_state, vecN_state, vecM_state = (
                c_initial.to(dtype=dtype_state),
                n_initial.to(dtype=dtype_state),
                m_initial.to(dtype=dtype_state),
            )
        else:
            # memory state
            matC_state = torch.zeros((batch_size, nh, dhqk, dhv), dtype=dtype_state, device=device)
            # normalizer state
            vecN_state = torch.zeros((batch_size, nh, dhqk), dtype=dtype_state, device=device)
            # max state
            vecM_state = torch.zeros((batch_size, nh, 1), dtype=dtype_state, device=device)

        vecH_list = []
        for t in range(sequence_length):
            # gates
            vecF_t, vecI_t = fgate[:, :, t, None], igate[:, :, t, None]

            # projections
            vecQ_t, vecK_t, vecV_t = query[:, :, t, :], key[:, :, t, :], value[:, :, t, :]

            # step
            vecH, (matC_state, vecN_state, vecM_state) = mlstm_recurrent_step_native(
                cstate=matC_state,
                nstate=vecN_state,
                mstate=vecM_state,
                query=vecQ_t,
                key=vecK_t,
                value=vecV_t,
                igate=vecI_t,
                fgate=vecF_t,
                eps=eps,
                dtype_state=dtype_state,
                **kwargs,
            )
            vecH_list.append(vecH)

        matH = torch.stack(vecH_list, dim=-2)

        if return_last_states:
            return matH, (matC_state, vecN_state, vecM_state)
        else:
            return matH