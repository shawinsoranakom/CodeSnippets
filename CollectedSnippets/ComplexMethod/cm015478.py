def _test_structured_input_output(
        self,
        container_type: str,
        mp_config: tuple[torch.dtype | None, torch.dtype | None],
    ):
        param_dtype, reduce_dtype = mp_config

        @dataclasses.dataclass
        class DC:
            x: torch.Tensor
            y: torch.Tensor

        @dataclasses.dataclass
        class Inner:
            x: torch.Tensor
            y: torch.Tensor

        @dataclasses.dataclass
        class Outer:
            inner: Inner
            z: torch.Tensor

        class TensorPair(NamedTuple):
            x: torch.Tensor
            y: torch.Tensor

        class ContainerModule(nn.Module):
            """Applies a linear layer to each tensor in the container."""

            def __init__(self, ctype: str, dim: int):
                super().__init__()
                self.ctype = ctype
                self._layer = nn.Linear(dim, dim)

            def forward(self, inp: Any) -> Any:
                if self.ctype == "dataclass":
                    return DC(x=self._layer(inp.x), y=self._layer(inp.y))
                elif self.ctype == "nested_dataclass":
                    return Outer(
                        inner=Inner(
                            x=self._layer(inp.inner.x),
                            y=self._layer(inp.inner.y),
                        ),
                        z=self._layer(inp.z),
                    )
                else:  # namedtuple
                    return TensorPair(x=self._layer(inp.x), y=self._layer(inp.y))

        class ToContainer(nn.Module):
            """Converts a plain tensor into a structured container."""

            def __init__(self, ctype: str):
                super().__init__()
                self.ctype = ctype

            def forward(self, x: torch.Tensor) -> Any:
                # clone() so each field has an independent autograd path
                if self.ctype == "dataclass":
                    return DC(x=x, y=x.clone())
                elif self.ctype == "nested_dataclass":
                    return Outer(inner=Inner(x=x, y=x.clone()), z=x.clone())
                else:  # namedtuple
                    return TensorPair(x=x, y=x.clone())

        class FromContainer(nn.Module):
            """Extracts and sums tensors from a structured container."""

            def __init__(self, ctype: str):
                super().__init__()
                self.ctype = ctype

            def forward(self, inp: Any) -> torch.Tensor:
                if self.ctype == "nested_dataclass":
                    return inp.inner.x + inp.inner.y + inp.z
                else:
                    return inp.x + inp.y

        torch.manual_seed(42)
        dim = 16
        local_batch_size = 2
        global_batch_size = self.world_size * local_batch_size

        model = nn.Sequential(
            ToContainer(container_type),
            ContainerModule(container_type, dim),
            ContainerModule(container_type, dim),
            FromContainer(container_type),
        )
        ref_model = copy.deepcopy(model).to(device_type)

        mp_policy = MixedPrecisionPolicy(
            param_dtype=param_dtype, reduce_dtype=reduce_dtype
        )
        for module in model:
            fully_shard(module, mp_policy=mp_policy)
        fully_shard(model, mp_policy=mp_policy)

        if param_dtype is not None:
            # Maintain a bf16 copy for compute, fp32 copy for optimizer
            ref_model_compute = copy.deepcopy(ref_model).to(param_dtype)
        ref_optim = torch.optim.Adam(ref_model.parameters(), lr=1e-2)
        optim = torch.optim.Adam(model.parameters(), lr=1e-2)

        torch.manual_seed(1)  # same on all ranks
        for iter_idx in range(10):
            global_inp = torch.rand((global_batch_size, dim), device=device_type.type)
            local_inp = global_inp[
                self.rank * local_batch_size : (self.rank + 1) * local_batch_size
            ].detach()

            # FSDP forward/backward
            optim.zero_grad(set_to_none=(iter_idx % 2 == 0))
            fsdp_loss = model(local_inp).sum()
            fsdp_loss.backward()
            optim.step()

            # Ref forward/backward
            ref_optim.zero_grad(set_to_none=(iter_idx % 2 == 0))
            if param_dtype is not None:
                ref_loss = ref_model_compute(global_inp.to(param_dtype)).sum()
                ref_loss.backward()
                # Simulate gradient reduction matching FSDP's behavior
                if reduce_dtype is not None and reduce_dtype != param_dtype:
                    # Cast grads to reduce_dtype, all-reduce, divide
                    for p in ref_model_compute.parameters():
                        p.grad.data = p.grad.to(reduce_dtype)
                        dist.all_reduce(p.grad)
                        p.grad.div_(self.world_size)
                else:
                    self._reduce_1d_partial_grads(ref_model_compute)
                for p_fp32, p_compute in zip(
                    ref_model.parameters(), ref_model_compute.parameters()
                ):
                    p_fp32.grad = p_compute.grad.to(p_fp32.dtype)
                    p_compute.grad = None
                ref_optim.step()
                for p_fp32, p_compute in zip(
                    ref_model.parameters(), ref_model_compute.parameters()
                ):
                    p_compute.detach().copy_(p_fp32)
            else:
                ref_loss = ref_model(global_inp).sum()
                ref_loss.backward()
                self._reduce_1d_partial_grads(ref_model)
                ref_optim.step()

            dist.all_reduce(fsdp_loss)  # partial -> replicated
            self.assertEqual(fsdp_loss, ref_loss)
            # bf16 gradient accumulation introduces drift beyond default
            # fp32 tolerances, so only check full param/grad parity for fp32.
            if param_dtype is None:
                check_sharded_parity(self, ref_model, model)