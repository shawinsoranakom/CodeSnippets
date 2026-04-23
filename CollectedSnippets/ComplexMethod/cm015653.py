def test_cross_compile_realistic_transformer_model(self):
        """
        Test cross-compilation with transformer model with DTensors,
        FlexAttention, and checkpointing using the compiler toolkit.
        Compares compiled execution against eager execution for bitwise
        equivalence of logits and gradients.
        """
        from torch.distributed._tensor import DTensor
        from torch.distributed.device_mesh import init_device_mesh
        from torch.distributed.tensor import Placement, Replicate, Shard
        from torch.testing._internal.distributed.fake_pg import FakeStore

        def dtensorify_module(
            module: nn.Module,
            device_mesh,
            *,
            param_placements: list[Placement] | None = None,
            buffer_placements: list[Placement] | None = None,
        ) -> None:
            if param_placements is None:
                param_placements = [Replicate()]
            if buffer_placements is None:
                buffer_placements = [Replicate()]

            for name, p in list(module.named_parameters(recurse=False)):
                if p is None or isinstance(p, DTensor):
                    continue
                dt = DTensor.from_local(p.data, device_mesh, param_placements)
                new_p = nn.Parameter(dt, requires_grad=p.requires_grad)
                setattr(module, name, new_p)

            for name, b in list(module.named_buffers(recurse=False)):
                if b is None or isinstance(b, DTensor):
                    continue
                dt = DTensor.from_local(b, device_mesh, buffer_placements)
                module._buffers[name] = dt

            for child in module.children():
                dtensorify_module(
                    child,
                    device_mesh,
                    param_placements=param_placements,
                    buffer_placements=buffer_placements,
                )

        def init_weights_deterministic(module: nn.Module, seed: int = 42) -> None:
            """
            Initialize module weights deterministically using a fixed seed.
            This ensures reproducible results across eager and compiled runs.
            """
            torch.manual_seed(seed)
            getattr(torch, GPU_TYPE).manual_seed(seed)
            for name, param in module.named_parameters():
                if param.requires_grad:
                    local_param = (
                        param.to_local() if isinstance(param, DTensor) else param
                    )
                    local_param.data.normal_(mean=0.0, std=0.02)
            for name, buf in module.named_buffers():
                local_buf = buf.to_local() if isinstance(buf, DTensor) else buf
                local_buf.data.normal_(mean=0.0, std=0.02)

        fake_store = FakeStore()
        c10d.init_process_group(backend="fake", store=fake_store, rank=0, world_size=1)

        try:
            rank = c10d.get_rank()
            device = torch.device(f"{GPU_TYPE}:{rank}")
            vocab_size = 1000
            embed_dim = 256
            num_heads = 8
            num_kv_heads = 2
            num_layers = 2
            max_seq_len = 32
            batch_size = 2
            seq_len = 16

            device_mesh = init_device_mesh(
                GPU_TYPE,
                (1,),
                mesh_dim_names=("dp",),
            )

            with torch.device("meta"):
                model = Transformer(
                    vocab_size,
                    embed_dim,
                    num_heads,
                    num_layers,
                    max_seq_len,
                    num_kv_heads=num_kv_heads,
                    device_mesh=device_mesh,
                )

            dtensorify_module(
                model,
                device_mesh,
                param_placements=[Replicate()],
                buffer_placements=[Replicate()],
            )

            outer_fake_mode = FakeTensorMode(allow_non_fake_inputs=True)
            with outer_fake_mode:
                # Convert meta tensors -> fake tensors on target device
                model.to_empty(device=device)

                local_input_ids = torch.randint(
                    0, vocab_size, (batch_size, seq_len), device=device
                )
                input_ids_dt = DTensor.from_local(
                    local_input_ids, device_mesh, [Shard(0)]
                )

            from torch._dynamo.functional_export import dynamo_graph_capture_for_export

            gm = dynamo_graph_capture_for_export(model)(input_ids_dt)

            fake_mode = gm.meta["fake_mode"]

            # Pre-create a temp file path and remove delete=False since we control cleanup
            with (
                tempfile.NamedTemporaryFile(suffix=".pt") as f,
                torch._functorch.config.patch(force_autograd_cache=True),
            ):
                serialization_path = f.name

                with contextlib.ExitStack() as stack:
                    if fake_mode is not None:
                        stack.enter_context(tracing(TracingContext(fake_mode)))
                        stack.enter_context(fake_mode)

                    jd = aot_export_joint_with_descriptors(
                        stack,
                        gm,
                        (input_ids_dt,),
                    )

                    compiled_wrapper = aot_compile_joint_with_descriptors(
                        jd,
                        fw_compiler=regional_inductor,
                        bw_compiler=regional_inductor,
                        serializable=True,
                    )

                    f.write(
                        BundledAOTAutogradSerializableCallable.serialize_compile_artifacts(
                            compiled_wrapper
                        )
                    )
                    f.flush()

                with open(serialization_path, "rb") as f_r:
                    loaded_fn = BundledAOTAutogradSerializableCallable.deserialize_compile_artifacts(
                        f_r.read()
                    )

                # Create compiled model with deterministic initialization
                local_input_ids = torch.randint(
                    0, vocab_size, (batch_size, seq_len), device=device
                )
                input_ids_dt = DTensor.from_local(
                    local_input_ids, device_mesh, [Shard(0)]
                )
                targets = torch.randint(
                    0, vocab_size, (batch_size, seq_len), device=device
                )

                compiled_model = Transformer(
                    vocab_size,
                    embed_dim,
                    num_heads,
                    num_layers,
                    max_seq_len,
                    num_kv_heads=num_kv_heads,
                    device_mesh=device_mesh,
                )
                dtensorify_module(
                    compiled_model,
                    device_mesh,
                    param_placements=[Replicate()],
                    buffer_placements=[Replicate()],
                )
                compiled_model.to_empty(device=device)
                init_weights_deterministic(compiled_model)

                eager_model = Transformer(
                    vocab_size,
                    embed_dim,
                    num_heads,
                    num_layers,
                    max_seq_len,
                    num_kv_heads=num_kv_heads,
                    device_mesh=device_mesh,
                )
                dtensorify_module(
                    eager_model,
                    device_mesh,
                    param_placements=[Replicate()],
                    buffer_placements=[Replicate()],
                )
                eager_model.to_empty(device=device)
                init_weights_deterministic(eager_model)

                # Run compiled forward pass
                (compiled_logits_dt,) = loaded_fn(
                    *compiled_model.parameters(),
                    *compiled_model.buffers(),
                    input_ids_dt,
                )
                compiled_logits = (
                    compiled_logits_dt.to_local()
                    if isinstance(compiled_logits_dt, DTensor)
                    else compiled_logits_dt
                )

                # Run eager forward pass with same input
                eager_logits_dt = eager_model(input_ids_dt)
                eager_logits = (
                    eager_logits_dt.to_local()
                    if isinstance(eager_logits_dt, DTensor)
                    else eager_logits_dt
                )

                # Compare logits for bitwise equivalence
                self.assertEqual(
                    compiled_logits,
                    eager_logits,
                    msg="Compiled and eager logits should be bitwise equivalent",
                )

                # Run backward pass on compiled model
                compiled_loss = F.cross_entropy(
                    compiled_logits.view(-1, vocab_size), targets.view(-1)
                )
                compiled_loss.backward()
                compiled_grads = {
                    name: p.grad.clone() if p.grad is not None else None
                    for name, p in compiled_model.named_parameters()
                }

                # Run backward pass on eager model
                eager_loss = F.cross_entropy(
                    eager_logits.view(-1, vocab_size), targets.view(-1)
                )
                eager_loss.backward()
                eager_grads = {
                    name: p.grad.clone() if p.grad is not None else None
                    for name, p in eager_model.named_parameters()
                }

                # Compare losses for bitwise equivalence
                self.assertEqual(
                    compiled_loss,
                    eager_loss,
                    msg="Compiled and eager losses should be bitwise equivalent",
                )

                # Compare gradients for bitwise equivalence
                for name in compiled_grads:
                    self.assertEqual(
                        compiled_grads[name],
                        eager_grads[name],
                        msg=f"Gradients for {name} should be bitwise equivalent",
                    )
        finally:
            c10d.destroy_process_group()