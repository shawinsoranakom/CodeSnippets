def update_mask(  # type: ignore[call-override, override]
        self,
        module,
        tensor_name,
        sparsity_level,
        sparse_block_shape,
        zeros_per_block,
        **kwargs,
    ):
        values_per_block = reduce(operator.mul, sparse_block_shape)
        if zeros_per_block > values_per_block:
            raise ValueError(
                "Number of zeros per block cannot be more than the total number of elements in that block."
            )
        if zeros_per_block < 0:
            raise ValueError("Number of zeros per block should be positive.")

        mask = getattr(module.parametrizations, tensor_name)[0].mask
        if sparsity_level <= 0 or zeros_per_block == 0:
            mask.data = torch.ones_like(mask)
        elif sparsity_level >= 1.0 and (zeros_per_block == values_per_block):
            mask.data = torch.zeros_like(mask)
        else:
            ww = self.norm_fn(getattr(module, tensor_name))
            tensor_mask = self._make_tensor_mask(
                data=ww,
                input_shape=ww.shape,
                sparsity_level=sparsity_level,
                sparse_block_shape=sparse_block_shape,
            )
            if values_per_block != zeros_per_block:
                block_mask = self._make_block_mask(
                    data=ww,
                    sparse_block_shape=sparse_block_shape,
                    zeros_per_block=zeros_per_block,
                )
                tensor_mask = torch.logical_or(tensor_mask, block_mask)
            mask.data = tensor_mask