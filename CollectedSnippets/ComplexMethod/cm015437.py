def _test_train_parity_with_activation_checkpointing(
        self,
        checkpoint_impl: str,
        module_grouping: str,
        test_device_type: str,
    ):
        if checkpoint_impl not in ("composable", "utils", "wrapper"):
            raise AssertionError(f"Unexpected checkpoint_impl: {checkpoint_impl}")
        testing_compile = (
            replicate is not torch.distributed._composable.replicate_with_fsdp
        )
        if testing_compile and checkpoint_impl == "composable":
            return
        torch.manual_seed(42)
        vocab_size = 1024
        with torch.device(device_type):
            model_args = ModelArgs(
                n_layers=3,
                n_heads=4,
                vocab_size=vocab_size,
                max_seq_len=64,
                dropout_p=0,
                checkpoint_activations=(checkpoint_impl == "utils"),
                # For the mem-efficient module grouping, we separate the
                # embeddings from the output projection, which does not support
                # weight tying
                weight_tying=module_grouping != "mem_eff",
            )
            model = Transformer(model_args)
        ref_model = copy.deepcopy(model).to(device_type)
        ref_optim = torch.optim.Adam(ref_model.parameters(), lr=1e-2)

        # Apply activation checkpointing
        prefixes_to_ignore = ()
        if checkpoint_impl == "wrapper":
            prefixes_to_ignore = (_CHECKPOINT_PREFIX,)
            apply_activation_checkpointing(
                model, check_fn=lambda m: isinstance(m, TransformerBlock)
            )
        elif checkpoint_impl == "composable":
            for module in model.modules():
                if isinstance(module, TransformerBlock):
                    checkpoint(module)

        # Apply Replicate
        device_mesh = init_device_mesh(
            test_device_type,
            (self.world_size,),
            mesh_dim_names=("replicate",),
        )
        fsdp_kwargs = {
            "mesh": device_mesh,
        }
        if module_grouping == "mem_eff":
            if not (model_args.n_layers == 3):
                raise AssertionError(
                    f"Expected n_layers == 3, got {model_args.n_layers}"
                )
            replicate(model.layers[0], **fsdp_kwargs)
            replicate([model.layers[1], model.layers[2]], **fsdp_kwargs)
            replicate([model.tok_embeddings, model.pos_embeddings], **fsdp_kwargs)
            # Embedding weights are not needed for embedding backward
            model.tok_embeddings.set_unshard_in_backward(False)
            replicate([model.norm, model.output], **fsdp_kwargs)
        elif module_grouping == "mem_eff_weight_tied":
            replicate([model.tok_embeddings, model.output], **fsdp_kwargs)
            for layer in model.layers:
                replicate(layer, **fsdp_kwargs)
        elif module_grouping == "block":
            for layer in model.layers:
                replicate(layer, **fsdp_kwargs)
        else:
            raise NotImplementedError(f"Unknown module grouping: {module_grouping}")
        replicate(model, **fsdp_kwargs)
        optim = torch.optim.Adam(model.parameters(), lr=1e-2)

        torch.manual_seed(42 + self.rank)
        # Reuse the same input across iterations to avoid loss explosion from
        # trying to learn from random inputs
        inp = torch.randint(0, vocab_size, (3, 64), device=device_type.type)
        check_sharded_parity(
            self, ref_model, model, prefixes_to_ignore=prefixes_to_ignore
        )
        for iter_idx in range(10):
            losses: list[torch.Tensor] = []
            for _model in (ref_model, model):
                torch.manual_seed(iter_idx + 1)  # for dropout determinism
                losses.append(_model(inp).sum())
                losses[-1].backward()

            for param in ref_model.parameters():
                if param.grad is not None:
                    dist.all_reduce(param.grad)
                    param.grad.div_(self.world_size)

            if not testing_compile:
                check_sharded_parity(
                    self, ref_model, model, prefixes_to_ignore=prefixes_to_ignore
                )
            self.assertEqual(losses[0], losses[1])
            for _optim in (ref_optim, optim):
                _optim.step()
                _optim.zero_grad(set_to_none=(iter_idx % 2 == 0))
            if not testing_compile:
                check_sharded_parity(
                    self, ref_model, model, prefixes_to_ignore=prefixes_to_ignore
                )