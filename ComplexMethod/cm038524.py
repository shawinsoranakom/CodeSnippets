def all_reduce(self, input_):
        # since currently we perform copy input -> symm_input -> out-of-place AR
        # return symm_output, we don't need to check if input is symmetric
        if self.pynccl_comm is not None and should_nccl_symm_mem_allreduce(
            self.pynccl_comm.world_size, input_
        ):
            out = torch.ops.vllm.all_reduce_symmetric_with_copy(input_)
            if out is not None:
                return out
        # always try quick reduce first, then flashinfer, then custom allreduce,
        # and then pynccl. (quick reduce just for ROCM MI3*)
        qr_comm = self.qr_comm
        if (
            qr_comm is not None
            and not qr_comm.disabled
            and qr_comm.should_quick_allreduce(input_)
        ):
            out = qr_comm.quick_all_reduce(input_)
            assert out is not None
            return out
        fi_ar_comm = self.fi_ar_comm
        if (
            fi_ar_comm is not None
            and not fi_ar_comm.disabled
            and fi_ar_comm.should_use_fi_ar(input_)
        ):
            out = fi_ar_comm.all_reduce(input_)
            assert out is not None
            return out
        ca_comm = self.ca_comm
        if (
            ca_comm is not None
            and not ca_comm.disabled
            and ca_comm.should_custom_ar(input_)
        ):
            out = ca_comm.custom_all_reduce(input_)
            assert out is not None
            return out
        symm_mem_comm = self.symm_mem_comm
        if symm_mem_comm is not None and symm_mem_comm.should_use_symm_mem(input_):
            out = symm_mem_comm.all_reduce(input_)
            assert out is not None
            return out
        pynccl_comm = self.pynccl_comm
        if pynccl_comm is None or pynccl_comm.disabled:
            out = input_.clone()
            torch.distributed.all_reduce(out, group=self.device_group)
            return out
        assert pynccl_comm is not None
        out = pynccl_comm.all_reduce(input_)
        if out is None:
            # fall back to the default all-reduce using PyTorch.
            # this usually happens during testing.
            # when we run the model, allreduce only happens for the TP
            # group, where we always have either custom allreduce or pynccl.
            out = input_.clone()
            torch.distributed.all_reduce(out, group=self.device_group)
        return out