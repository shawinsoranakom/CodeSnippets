def __init__(
        self,
        config: Llama4TextConfig,
        overlap_router_shared = False,
        verbose = False,
        debug = False,
    ):
        super().__init__(config)
        self.overlap_router_shared = overlap_router_shared
        self.verbose = verbose
        self.debug = debug

        # Permute in-place expert weights
        E, K, N = self.num_experts, self.hidden_dim, self.experts.expert_dim
        assert self.experts.gate_up_proj.shape == torch.Size(
            [E, K, 2 * N]
        ), f"{self.experts.gate_up_proj.shape} != {[E, K, 2 * N]}"
        permuted_shape = [E, 2 * N, K]
        permuted_stride = [2 * N * K, K, 1]
        if verbose:
            print(
                f"Changing gate_up_proj from {self.experts.gate_up_proj.size()}:{self.experts.gate_up_proj.stride()} to {permuted_shape}:{permuted_stride}"
            )
        with torch.no_grad():
            self.experts.gate_up_proj.as_strided_(permuted_shape, permuted_stride)

        if verbose:
            print(
                f"{self.experts.gate_up_proj.shape}:{self.experts.gate_up_proj.stride()}"
            )

        assert self.experts.down_proj.shape == torch.Size(
            [E, N, K]
        ), f"{self.experts.down_proj.shape} != {[E, N, K]}"
        permuted_shape = [E, K, N]
        permuted_stride = [K * N, N, 1]
        if verbose:
            print(
                f"Changing down_proj from {self.experts.down_proj.size()}:{self.experts.down_proj.stride()} to {permuted_shape}:{permuted_stride}"
            )

        with torch.no_grad():
            self.experts.down_proj.as_strided_(permuted_shape, permuted_stride)

        if verbose:
            print(f"{self.experts.down_proj.shape}:{self.experts.down_proj.stride()}")

        if overlap_router_shared:
            self.shared_expert_stream = torch.cuda.Stream()
            self.default_event = torch.cuda.Event()
            self.shared_expert_end_event = torch.cuda.Event()