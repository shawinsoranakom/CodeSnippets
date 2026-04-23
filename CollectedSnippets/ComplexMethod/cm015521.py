def _test_unshard_params_recurse(
        self,
        recurse: bool,
        unshard_outer: bool,
        mixed_precision: MixedPrecision | None,
        use_orig_params: bool,
    ):
        """NOTE: This method depends on FSDP internals."""
        fsdp_kwargs = {
            "mixed_precision": mixed_precision,
            "use_orig_params": use_orig_params,
        }
        model = FSDP(
            nn.Sequential(
                FSDP(
                    nn.Linear(5, 5, bias=False, device=device_type.type), **fsdp_kwargs
                ),
                nn.Linear(5, 3, bias=False, device=device_type.type),
            ),
            **fsdp_kwargs,
        )
        # Hard code the numel values based on the model
        unsharded_inner_numel = 5 * 5
        unsharded_outer_numel = 5 * 3
        if use_orig_params:
            # Account for unsharded padding: since each `FlatParameter` only
            # has one original parameter, we only need to pad for divisibility
            # by world size and not address alignment
            if unsharded_inner_numel % self.world_size:
                unsharded_inner_numel += self.world_size - (
                    unsharded_inner_numel % self.world_size
                )
            if unsharded_outer_numel % self.world_size:
                unsharded_outer_numel += self.world_size - (
                    unsharded_outer_numel % self.world_size
                )
        # Round up the sharded numel to account for padding
        sharded_inner_numel = int(math.ceil(unsharded_inner_numel / self.world_size))
        sharded_outer_numel = int(math.ceil(unsharded_outer_numel / self.world_size))
        inner_flat_param = model.module[0]._handle.flat_param
        outer_flat_param = model._handle.flat_param
        self.assertEqual(sharded_inner_numel, inner_flat_param.numel())
        self.assertEqual(sharded_outer_numel, outer_flat_param.numel())
        expected_outer_numel = (
            unsharded_outer_numel if unshard_outer else sharded_outer_numel
        )
        expected_inner_numel = (
            unsharded_inner_numel
            if recurse or not unshard_outer
            else sharded_inner_numel
        )
        module_to_unshard = model if unshard_outer else model[0]
        with FSDP.summon_full_params(module_to_unshard, recurse=recurse):
            self.assertEqual(expected_outer_numel, outer_flat_param.numel())
            self.assertEqual(expected_inner_numel, inner_flat_param.numel())