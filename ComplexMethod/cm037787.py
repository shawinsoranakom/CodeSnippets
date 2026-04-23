def process_weights_after_loading(self, layer: torch.nn.Module) -> None:
        super().process_weights_after_loading(layer)

        # Padding the weight for better performance on ROCm
        layer.w13_weight.data = self._maybe_pad_weight(layer.w13_weight.data)
        layer.w2_weight.data = self._maybe_pad_weight(layer.w2_weight.data)

        if self.unquantized_backend in [
            UnquantizedMoeBackend.TPU,
            UnquantizedMoeBackend.OOT,
        ]:
            # OOT handles internally.
            return

        elif self.unquantized_backend == UnquantizedMoeBackend.CPU:
            # CPU stays on the old path — no oracle, no moe_kernel.
            from vllm.model_executor.layers.fused_moe import cpu_fused_moe

            if current_platform.get_cpu_architecture() == CpuArchEnum.X86:
                from vllm.model_executor.layers.utils import check_cpu_sgl_kernel

                dtype_w13 = layer.w13_weight.dtype
                _, n_w13, k_w13 = layer.w13_weight.size()
                dtype_w2 = layer.w2_weight.dtype
                _, n_w2, k_w2 = layer.w2_weight.size()
                if (
                    envs.VLLM_CPU_SGL_KERNEL
                    and check_cpu_sgl_kernel(n_w13, k_w13, dtype_w13)
                    and check_cpu_sgl_kernel(n_w2, k_w2, dtype_w2)
                ):
                    packed_w13_weight = torch.ops._C.convert_weight_packed(
                        layer.w13_weight
                    )
                    assert packed_w13_weight.size() == layer.w13_weight.size()
                    layer.w13_weight.copy_(packed_w13_weight)
                    del packed_w13_weight
                    packed_w2_weight = torch.ops._C.convert_weight_packed(
                        layer.w2_weight
                    )
                    assert packed_w2_weight.size() == layer.w2_weight.size()
                    layer.w2_weight.copy_(packed_w2_weight)
                    self.cpu_fused_moe: Callable = cpu_fused_moe.SGLFusedMOE(layer)
                else:
                    self.cpu_fused_moe = cpu_fused_moe.CPUFusedMOE(layer)
            else:
                self.cpu_fused_moe = cpu_fused_moe.CPUFusedMOE(layer)
        elif self.unquantized_backend == UnquantizedMoeBackend.XPU:
            w13 = layer.w13_weight
            w2 = layer.w2_weight

            w13.data = w13.transpose(-1, -2).contiguous()
            w2.data = w2.transpose(-1, -2).contiguous()

            self._setup_kernel(
                layer=layer,
                w13=w13,
                w2=w2,
            )
        else:
            self._setup_kernel(
                layer=layer,
                w13=layer.w13_weight,
                w2=layer.w2_weight,
            )