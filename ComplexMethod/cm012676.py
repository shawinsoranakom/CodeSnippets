def select_dispatch_strategy(self) -> None:
        if self.dispatch_class is not None:
            return
        if config.combo_kernel_per_subkernel_blocks:
            self.dispatch_class = ComboKernel.SequentialFlattenGridDispatch
            return
        # mixed_sizes is used for optimize_mask, so it only allows sequential dispatch
        # Not mixed sizes on y dim technically is ok to use round robin as wells.
        if not self.mixed_sizes or any(isinstance(e, str) for e in self.x_numels_list):
            # str in x_numels_list means a dynamic shape
            self.dispatch_class = ComboKernel.SequentialDispatch
            return
        # A negative x_blocks_list element means the kernel is not tunable,
        # i.e., no_x_dim = True
        x_numels_list = [abs(cast(int, e)) for e in self.x_numels_list]
        total = max(x_numels_list) * len(x_numels_list)
        needed = sum(x_numels_list)
        if needed / total > BLOCK_UTILIZATION:
            # Introduced overhead (masked blocks) is less than 20%
            self.dispatch_class = ComboKernel.RoundRobinDispatch
        else:
            self.dispatch_class = ComboKernel.SequentialDispatch