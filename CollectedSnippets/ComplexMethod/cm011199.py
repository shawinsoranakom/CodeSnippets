def torch_manual_seed(seed) -> torch._C.Generator:
        """LocalTensor-aware version of torch.random.manual_seed."""
        if (
            (lm := enabled_local_tensor_mode())
            and isinstance(seed, torch.SymInt)
            and isinstance(seed.node, LocalIntNode)
        ):
            from torch.random import _manual_seed_impl

            for rank in sorted(lm.ranks):
                rank_seed = seed.node._local_ints[rank]
                _manual_seed_impl(rank_seed)
                lm._per_rank_rng_states[rank] = _get_rng_state()
            return torch.random.default_generator
        from torch.random import _manual_seed_impl

        result = _manual_seed_impl(seed)

        if lm is not None and len(lm._per_rank_rng_states) > 0:
            cpu_state, cuda_states = _get_rng_state()
            for rank in lm.ranks:
                lm._per_rank_rng_states[rank] = (
                    cpu_state.clone(),
                    {idx: state.clone() for idx, state in cuda_states.items()},
                )

        return result