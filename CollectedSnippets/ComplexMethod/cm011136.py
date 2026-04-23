def init_unsharded_param(self):
        if hasattr(self, "_unsharded_param"):  # after the 1st all-gather
            inner_tensor = self._sharded_local_tensor
            if not hasattr(inner_tensor, "fsdp_post_all_gather"):
                return  # already initialized
            for tensor in self._unsharded_inner_tensors:
                alloc_storage(tensor)
            all_gather_outputs = self._unflatten_all_gather_outputs()
            inner_tensor.fsdp_post_all_gather(
                all_gather_outputs,
                self._extensions_data.all_gather_metadata,
                self.param_dtype or self.orig_dtype,
                out=self._unsharded_param,
            )
            self._extensions_data.clear()
            return
        inner_tensor = self._sharded_local_tensor
        if hasattr(inner_tensor, "fsdp_post_all_gather"):
            all_gather_outputs = self._unflatten_all_gather_outputs()
            (
                unsharded_tensor,
                self._unsharded_inner_tensors,
            ) = inner_tensor.fsdp_post_all_gather(
                all_gather_outputs,
                self._extensions_data.all_gather_metadata,
                self.param_dtype or self.orig_dtype,
            )
            self._extensions_data.clear()
        else:
            # For the default path (no post-all-gather), the all-gather output
            # gives the unsharded parameter data directly
            if len(self.all_gather_outputs) != 1:
                raise AssertionError(
                    f"Expected 1 all_gather_output, got {len(self.all_gather_outputs)}"
                )
            unsharded_tensor = self.all_gather_outputs[0]
        unsharded_param = torch.as_strided(
            unsharded_tensor,
            self._orig_size,
            self._contiguous_orig_stride,
            storage_offset=0,
        )
        if self._unsharded_dtensor_spec is not None:
            unsharded_param = _from_local_no_grad(
                unsharded_param, self._unsharded_dtensor_spec
            )
        self._unsharded_param = nn.Parameter(
            unsharded_param, requires_grad=self.sharded_param.requires_grad
        )