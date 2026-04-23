def _setup_fusion_hooks(self):
        """Set up epilogue/prologue render hooks and mark prologue buffers.

        Must be called during render() (inside V.kernel context), after
        _compute_fusion_metadata has run.
        """
        tb = self._template_buffer

        # Mark prologue buffers on the kernel.
        for pro_buf, source_bufs in self._prologue_sources.items():
            self.store_buffer_names.add(pro_buf)
            if not source_bufs:
                self.removed_buffers.add(pro_buf)

        # Set up epilogue hooks.
        epilogues = self._eligible_epilogues
        for epilogue_idx in range(len(tb.epilogue_fusable_outputs)):
            epi = epilogues[epilogue_idx] if epilogue_idx < len(epilogues) else None
            self._setup_epilogue_hook(
                output_buf=epi[1] if epi else None,
                output_param=epi[2] if epi else None,
            )

        # Set up prologue hooks.
        for param_name in tb._named_inputs:
            self._setup_prologue_hook(
                param_name, prologue_sources=self._prologue_sources
            )

        # Register no-op <DEF_KERNEL> hook (standard path requires it).
        self.render_hooks["<DEF_KERNEL>"] = lambda: ""