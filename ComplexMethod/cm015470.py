def _test_state_dict_save_load(self, model: nn.Module):
        for param_name, param in model.named_parameters():
            self.assertIsInstance(
                param,
                DTensor,
                f"Expects parameters to be sharded as DTensors but got {param_name} "
                f"as {type(param)}: {param}",
            )
        old_fill_value = 1
        new_fill_value = 42 + self.rank
        with torch.no_grad():
            for param in model.parameters():
                param.fill_(old_fill_value)
        # Use that the parameters are currently sharded, meaning that their
        # data pointers correspond to the sharded parameter data
        param_name_to_data_ptr = {
            n: p.to_local().data_ptr() for n, p in model.named_parameters()
        }
        ref_sharded_sizes = [p.size() for p in model.parameters()]
        state_dict = model.state_dict()
        for param, ref_sharded_size in zip(model.parameters(), ref_sharded_sizes):
            self.assertEqual(param.size(), ref_sharded_size)
            self.assertTrue(isinstance(param, nn.Parameter))

        # Verify that keys match, values are DTensors, and values share the
        # same storage as the existing sharded parameter data
        self.assertEqual(set(state_dict.keys()), set(param_name_to_data_ptr.keys()))
        for param_name, tensor in state_dict.items():
            self.assertTrue(isinstance(tensor, DTensor))
            if param_name_to_data_ptr[param_name] == 0:
                # Check that this is padding (added by DTensor)
                self.assertGreater(self.rank, 0)
                self.assertEqual(torch.count_nonzero(tensor.to_local()).item(), 0)
            else:
                self.assertEqual(
                    tensor.to_local().data_ptr(), param_name_to_data_ptr[param_name]
                )

        # Verify that we can load a new state dict that contains DTensors with
        # storages different from the current model parameters
        new_state_dict: dict[str, DTensor] = {}
        for param_name, dtensor in state_dict.items():
            # Construct new DTensors to exercise load state dict writeback
            new_state_dict[param_name] = dtensor.detach().clone().fill_(new_fill_value)
        for param in model.parameters():
            self.assertEqual(
                param.to_local(),
                torch.ones_like(param.to_local()) * old_fill_value,
            )
        model.load_state_dict(new_state_dict)
        for param_name, param in model.named_parameters():
            self.assertEqual(
                param.to_local(),
                torch.ones_like(param.to_local()) * new_fill_value,
            )
            local_param = param.to_local()
            # Only guarantee that the local tensor's data pointer does not
            # change if the sharding was even (i.e. no padding); otherwise,
            # FSDP may re-pad the local tensor, changing its data pointer
            if local_param.size(0) * param.device_mesh.size() == param.size(0):
                self.assertEqual(
                    local_param.data_ptr(), param_name_to_data_ptr[param_name]
                )