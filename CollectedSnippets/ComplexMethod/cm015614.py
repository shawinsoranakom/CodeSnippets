def _compare_params(
        self,
        local_module,
        dist_module,
        rank0_only,
        skip_rowwise_bias=False,
        compare_grad=False,
    ):
        replicate = [Replicate()]
        for name, param in local_module.named_parameters():
            dist_param = dist_module.get_parameter(name)
            param = param.grad if compare_grad else param
            dist_param = dist_param.grad if compare_grad else dist_param
            if (
                (not rank0_only)
                or (self.rank == 0)
                or (
                    name != "net2.bias"
                    and not skip_rowwise_bias
                    or name not in ["bias", "net2.bias"]
                )
            ):
                self.assertEqual(
                    param,
                    dist_param.redistribute(
                        device_mesh=dist_param.device_mesh, placements=replicate
                    ).to_local(),
                    f"{name} not equal between dist and non-dist",
                )