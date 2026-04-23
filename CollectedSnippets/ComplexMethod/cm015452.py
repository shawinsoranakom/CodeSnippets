def test_param_registration_after_forward(self):
        """Tests the parameter registration after forward."""
        device = torch.device(device_type.type, 0)
        # Single FSDP group
        for reshard_after_forward in (True, False, 2, None):
            torch.manual_seed(42)
            model = MLP(3, device)
            # Since seed is per process, not per thread, we broadcast to ensure
            # the same parameters across ranks
            for param in model.parameters():
                dist.broadcast(param, src=0)
            ref_model = copy.deepcopy(model)
            fully_shard(model, reshard_after_forward=reshard_after_forward)  # root only
            inp = torch.randn((2, 3), device=device_type.type)
            self._assert_dtensor_params(model.parameters())
            self._assert_same_params(model.parameters(), ref_model.parameters())
            model(inp)
            if reshard_after_forward:
                self._assert_dtensor_params(model.parameters())
            else:
                self._assert_tensor_params(model.parameters())
            self._assert_same_params(model.parameters(), ref_model.parameters())
            model.reshard()  # however, we can manually reshard
            self._assert_dtensor_params(model.parameters())
            self._assert_same_params(model.parameters(), ref_model.parameters())

        # Multiple FSDP groups
        for reshard_after_forward in (True, False, 2, None):
            torch.manual_seed(42)
            model = nn.Sequential(MLP(3, device), MLP(3, device))
            for param in model.parameters():
                dist.broadcast(param, src=0)
            ref_model = copy.deepcopy(model)
            fully_shard(model[0].in_proj, reshard_after_forward=reshard_after_forward)
            fully_shard(model[0].out_proj, reshard_after_forward=reshard_after_forward)
            fully_shard(model, reshard_after_forward=reshard_after_forward)

            self._assert_dtensor_params(model.parameters())
            self._assert_same_params(model.parameters(), ref_model.parameters())
            model(inp)
            non_root_params = list(model[0].in_proj.parameters()) + list(
                model[0].out_proj.parameters()
            )
            root_params = list(set(model.parameters()) - set(non_root_params))
            if reshard_after_forward is None:
                self._assert_dtensor_params(non_root_params)
                self._assert_tensor_params(root_params)
            elif reshard_after_forward:
                self._assert_dtensor_params(non_root_params)
                self._assert_dtensor_params(root_params)
            else:
                self._assert_tensor_params(non_root_params)
                self._assert_tensor_params(root_params)
            self._assert_same_params(model.parameters(), ref_model.parameters())
            for module in model.modules():
                if isinstance(module, FSDPModule):
                    module.reshard()  # however, we can manually reshard
            self._assert_dtensor_params(model.parameters())
            self._assert_same_params(model.parameters(), ref_model.parameters())