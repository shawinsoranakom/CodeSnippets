def test_all_gather_extensions_monkey_patch(self):
        tls = threading.local()
        tls.ran_pre_all_gather = False

        # Define a pre/post-all-gather pair that quantizes to bf16 for the
        # all-gather and de-quantizes back to the parameter dtype
        def fsdp_pre_all_gather(
            self,
            mesh: DeviceMesh,
            outer_size: torch.Size,
            outer_stride: tuple[int, ...],
            module: nn.Module,
            mp_policy: MixedPrecisionPolicy,
        ) -> tuple[tuple[torch.Tensor, ...], Any]:
            nonlocal tls
            tls.ran_pre_all_gather = True
            return (self.to(torch.bfloat16),), None

        @torch.no_grad()
        def fsdp_post_all_gather(
            self,
            all_gather_outputs: tuple[torch.Tensor, ...],
            metadata: Any,
            param_dtype: torch.dtype,
            *,
            out: torch.Tensor | None = None,
        ) -> tuple[torch.Tensor, tuple[torch.Tensor, ...]] | None:
            (tensor,) = all_gather_outputs
            if metadata is not None:
                raise AssertionError(f"Expected metadata to be None, got {metadata}")
            if tensor.dtype != torch.bfloat16:
                raise AssertionError(
                    f"Expected tensor.dtype == torch.bfloat16, got {tensor.dtype}"
                )
            if out is not None:
                with _unsafe_preserve_version_counter(out):
                    out.copy_(tensor)
                return
            upcast_tensor = tensor.to(param_dtype)
            return upcast_tensor, (tensor, upcast_tensor)

        with torch.device("meta"):
            model = self._init_two_tensor_mlp()
        for mlp in model:
            fully_shard(mlp)
        fully_shard(model)
        model.to_empty(device=self.device)
        for param in model.parameters():
            nn.init.trunc_normal_(param)
        # Monkey patch the pre/post-all-gather functions *after* `to_empty()`
        # since the local tensor objects change from materialization
        self.assertGreater(sum("weight" in n for n, _ in model.named_parameters()), 0)
        for param_name, param in model.named_parameters():
            if "weight" in param_name:
                # Need to use `_local_tensor` to patch the tensor object
                local_param = param._local_tensor
                # Monkey patch on the `torch.Tensor` as instance methods to
                # show that the extension can work even without a subclass
                local_param.fsdp_pre_all_gather = fsdp_pre_all_gather.__get__(
                    local_param
                )
                local_param.fsdp_post_all_gather = fsdp_post_all_gather.__get__(
                    local_param
                )
        optim = torch.optim.Adam(model.parameters(), lr=1e-2, foreach=True)

        # Run a few iterations to check for errors
        torch.manual_seed(42 + self.rank + 1)
        inp = torch.randn((2, 8), device=device_type)
        for _ in range(3):
            model(inp).sum().backward()
            optim.step()
            optim.zero_grad()
        if not tls.ran_pre_all_gather:
            raise AssertionError("Expected tls.ran_pre_all_gather to be True")