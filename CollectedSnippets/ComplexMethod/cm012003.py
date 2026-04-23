def can_fuse_epilogue(self) -> bool:
        """
        For kernels like

        @triton.jit
        def add_kernel(in_ptr0, in_ptr1, out_ptr, n_elements, BLOCK_SIZE: tl.constexpr):
            pid = tl.program_id(0)
            offs = pid * BLOCK_SIZE + tl.arange(0, BLOCK_SIZE)
            mask = offs < n_elements
            x = tl.load(in_ptr0 + offs, mask=mask)
            y = tl.load(in_ptr1 + offs, mask=mask)
            tl.store(out_ptr + offs, x + y, mask=mask)

        @torch.compile
        def fn(a, b):
            out = torch.empty_like(a)
            grid = (triton.cdiv(a.numel(), 1024),)
            add_kernel[grid](a, b, out, a.numel(), BLOCK_SIZE=1024)
            return out.relu()

        We can potentially fuse the relu epilogue into the add_kernel.
        We do this by pruning the `out` tensor allocation and directly writing the relu-output.
        """

        if not config.epilogue_fusion_user_defined_triton_kernel:
            return False

        if not self.arg_accesses.can_fuse_epilogue:
            return False

        # We achieve fusion by parsing the original src into a python AST,
        # then identify the expr containing the original value written via tl.store().
        # We generate an expr for the value after the epilogue and replace that into the tl.store.
        # So far we only support the simple case where there is a single tl.store in the kernel.
        if len(self.kernel_stores.stores) != 1:
            return False

        # Only fuse if the mutated arg is originally an "empty" tensor.
        # This is because we don't know exactly which element of that tensor is being written to.
        # If the kernel only writes to a subset of the tensor, then we only apply the epilogue to that subset.
        # In these edge cases, our fusion is only correct if the original tensor is empty,
        # where the semantics is that content values are UB, and we can rely on the fact that `epilogue(UB) == UB`.
        assert len(self.mutable_args) == 1
        if not isinstance(self.mutable_args[0], TensorBox):
            return False
        if not isinstance(self.mutable_args[0].data, StorageBox):
            return False
        if not isinstance(self.mutable_args[0].data.data, ComputedBuffer):
            return False
        if not isinstance(self.mutable_args[0].data.data.data, Pointwise):
            return False
        if not all(r == 0 for r in self.mutable_args[0].data.data.data.ranges):
            return False

        return True