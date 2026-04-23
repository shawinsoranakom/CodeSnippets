def test_layer_norm_bwd(self):
        device_mesh = self.build_device_mesh()

        # NLP example from pytorch docs
        # https://pytorch.org/docs/stable/generated/torch.nn.LayerNorm.html
        batch, sentence_length, embedding_dim = 20, 5, 10
        norm_shape_idx_list = list(range(3))
        shard_dims = [0, 1, 2]
        elementwise_affine_list = [False, True]

        # Test both LayerNorm and RMSNorm (if CUDA)
        norm_types = [torch.nn.LayerNorm]
        if self.device_type == "cuda" and hasattr(torch.nn, "RMSNorm"):
            norm_types.append(torch.nn.RMSNorm)

        test_config_list = list(
            itertools.product(
                norm_types, shard_dims, norm_shape_idx_list, elementwise_affine_list
            )
        )

        # normalized shape is a torch.Size object
        for norm_type, shard_dim, norm_idx, elementwise_affine in test_config_list:
            x = torch.rand(
                batch,
                sentence_length,
                embedding_dim,
                device=self.device_type,
                requires_grad=True,
            )
            normalized_shape = x.shape[norm_idx:]
            layer_norm = norm_type(
                normalized_shape,
                elementwise_affine=elementwise_affine,
                device=self.device_type,
            )
            layer_norm_local = copy.deepcopy(layer_norm).to(self.device_type)

            def _replicate_fn(name, module, device_mesh):
                for name, param in module.named_parameters():
                    if name in ["weight", "bias"]:
                        param_dist = torch.nn.Parameter(
                            distribute_tensor(param, device_mesh, [Replicate()])
                        )
                        module.register_parameter(name, param_dist)

            layer_norm_dist = distribute_module(layer_norm, device_mesh, _replicate_fn)

            if elementwise_affine:
                self.assertEqual(
                    layer_norm_local.weight, layer_norm_dist.weight.full_tensor()
                )
                # RMSNorm doesn't have bias
                if hasattr(layer_norm_local, "bias"):
                    self.assertEqual(
                        layer_norm_local.bias, layer_norm_dist.bias.full_tensor()
                    )

            x_local = x.detach().clone().requires_grad_(True)
            x_dist = distribute_tensor(x, device_mesh, [Shard(shard_dim)])
            self.assertEqual(x_local, x_dist.full_tensor())

            y_local = layer_norm_local(x_local)
            # make sure that backward layer norm does not introduce extra collectives
            comm_mode = CommDebugMode()
            with comm_mode:
                y_dist = layer_norm_dist(x_dist)
                y_dist.sum().backward()

            expected_fwd_comm = 0 if shard_dim < norm_idx else 1

            self.assertEqual(
                sum(comm_mode.comm_module_counts["Global"]["forward"].values()),
                expected_fwd_comm,
                f"comm count={comm_mode.get_total_counts()}, norm_type={norm_type.__name__}, "
                f"shard_dim={shard_dim}, norm_shape={normalized_shape}, elem_affine={elementwise_affine}",
            )

            self.assertEqual(y_local, y_dist.full_tensor())

            # backward step
            y_local.sum().backward()

            expected_bwd_comm = 0 if shard_dim < norm_idx else 1

            self.assertEqual(
                sum(comm_mode.comm_module_counts["Global"]["backward"].values()),
                expected_bwd_comm,
                f"comm count={comm_mode.get_total_counts()}, norm_type={norm_type.__name__}, "
                f"shard_dim={shard_dim}, norm_shape={normalized_shape}, elem_affine={elementwise_affine}",
            )

            if elementwise_affine:
                # if input is sharded on any outer dimension, the gradient of weight
                # and bias should be Partial
                dim_map = x_dist._spec.dim_map
                outer_dims = range(norm_idx)
                needs_reduction = any(dim_map[d] >= 0 for d in outer_dims)
                self.assertEqual(
                    is_tensor_partial(layer_norm_dist.weight.grad._spec),
                    needs_reduction,
                )
                # RMSNorm doesn't have bias
                if hasattr(layer_norm_dist, "bias"):
                    self.assertEqual(
                        is_tensor_partial(layer_norm_dist.bias.grad._spec),
                        needs_reduction,
                    )
                self.assertEqual(
                    layer_norm_local.weight.grad,
                    layer_norm_dist.weight.grad.full_tensor(),
                )
                # RMSNorm doesn't have bias
                if hasattr(layer_norm_local, "bias"):
                    self.assertEqual(
                        layer_norm_local.bias.grad,
                        layer_norm_dist.bias.grad.full_tensor(),
                    )

            self.assertEqual(x_local.grad, x_dist.grad.full_tensor())