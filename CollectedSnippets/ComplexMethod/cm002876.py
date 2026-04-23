def mlstm_chunkwise_recurrent_fw_C(
        matK: torch.Tensor,
        matV: torch.Tensor,
        vecB: torch.Tensor,
        vecI: torch.Tensor,
        matC_states: torch.Tensor | None = None,
        vecN_states: torch.Tensor | None = None,
        scaMinter_states: torch.Tensor | None = None,
        matC_initial: torch.Tensor | None = None,
        vecN_initial: torch.Tensor | None = None,
        scaMinter_initial: torch.Tensor | None = None,
        qk_scale: float | None = None,
        chunk_size: int = 64,
        num_chunks: int = 1,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        batch_size, nh, _, dhqk, dhhv = *matK.shape, matV.shape[-1]
        nc = num_chunks
        _dtype, _device = matK.dtype, matK.device

        if qk_scale is None:
            qk_scale = dhqk**-0.5

        # initialize the states tensors
        if matC_states is None:
            matC_states = torch.zeros((batch_size, nh, (nc + 1) * dhqk, dhhv), dtype=_dtype, device=_device)
        if vecN_states is None:
            vecN_states = torch.zeros((batch_size, nh, (nc + 1) * dhqk), dtype=_dtype, device=_device)
        if scaMinter_states is None:
            scaMinter_states = torch.zeros((batch_size, nh, (nc + 1)), dtype=_dtype, device=_device)

        # assign the initial states to the running states
        matC_k = (
            torch.zeros((batch_size, nh, dhqk, dhhv), dtype=_dtype, device=_device)
            if matC_initial is None
            else matC_initial
        )
        vecN_k = (
            torch.zeros((batch_size, nh, dhqk), dtype=_dtype, device=_device) if vecN_initial is None else vecN_initial
        )
        scaM_inter_k = (
            torch.zeros((batch_size, nh, 1), dtype=_dtype, device=_device)
            if scaMinter_initial is None
            else scaMinter_initial
        )
        vecA = vecB[..., -1, None] - vecB + vecI
        scaG = vecB[..., -1]
        scaA_max = vecA.max(-1).values

        scaM_inter_k = scaM_inter_k.squeeze(-1)

        for key in range(0, num_chunks):
            # store the states from the previous iteration before updating them
            # in the first iteration, these are the initial states
            matC_states[:, :, key * dhqk : (key + 1) * dhqk, :] = matC_k
            vecN_states[:, :, key * dhqk : (key + 1) * dhqk] = vecN_k
            scaMinter_states[:, :, key] = scaM_inter_k

            # m_k update
            scaA_max_k = scaA_max[:, :, key]
            scaG_k = scaG[:, :, key]
            scaM_inter_k_next = torch.max(scaG_k + scaM_inter_k, scaA_max_k)
            # C_k update
            matK_chunk = matK[:, :, key * chunk_size : (key + 1) * chunk_size, :]  # * qk_scale
            matV_chunk = matV[:, :, key * chunk_size : (key + 1) * chunk_size, :]
            vecA_k = vecA[:, :, key, :]

            vecAbar_k = torch.exp(vecA_k - scaM_inter_k_next[..., None])[:, :, :, None]

            matK_chunk_gated = matK_chunk * vecAbar_k

            scaGbar_k = torch.exp(scaG_k + scaM_inter_k - scaM_inter_k_next)[:, :, None]

            # NOTE: no update in-place (i.e. +=) as this gives error for autograd backward
            matC_k_next = scaGbar_k[..., None] * matC_k + matK_chunk_gated.transpose(-2, -1) @ (matV_chunk)

            # n_k update
            vecN_k_next = scaGbar_k * vecN_k + matK_chunk_gated.transpose(-2, -1).sum(-1)

            # move to the next iteration
            scaM_inter_k = scaM_inter_k_next
            matC_k = matC_k_next
            vecN_k = vecN_k_next

        # store the states from the last iteration
        matC_states[:, :, -dhqk:, :] = matC_k
        vecN_states[:, :, -dhqk:] = vecN_k
        scaMinter_states[:, :, -1] = scaM_inter_k

        return matC_states, vecN_states, scaMinter_states