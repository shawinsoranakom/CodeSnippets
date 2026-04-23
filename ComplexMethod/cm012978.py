def update_mask(  # type: ignore[override]
        self, name, data, sparsity_level, sparse_block_shape, zeros_per_block, **kwargs
    ):
        values_per_block = reduce(operator.mul, sparse_block_shape)
        if zeros_per_block > values_per_block:
            raise ValueError(
                "Number of zeros per block cannot be more than "
                "the total number of elements in that block."
            )
        if zeros_per_block < 0:
            raise ValueError("Number of zeros per block should be positive.")

        if self.norm == "L1":
            data_norm = torch.abs(data).squeeze()  # absolute value based (L1)
        else:
            data_norm = (data * data).squeeze()  # square every element for L2

        if len(data_norm.shape) > 2:  # only supports 2 dimensional data at the moment
            raise ValueError("only supports 2-D at the moment")

        elif len(data_norm.shape) == 1:  # in case the data is bias (or 1D)
            data_norm = data_norm[None, :]

        mask = self.get_mask(name)
        if sparsity_level <= 0 or zeros_per_block == 0:
            mask.data = torch.ones_like(mask)
        elif sparsity_level >= 1.0 and (zeros_per_block == values_per_block):
            mask.data = torch.zeros_like(mask)

        # Fetch the high level mask that zeros out entire blocks
        data_lvl_mask = self.__get_data_level_mask(
            data=data_norm,
            sparsity_level=sparsity_level,
            sparse_block_shape=sparse_block_shape,
        )

        # Fetch block level mask that zeros out 'zeros_per_block' number of elements in every block
        block_lvl_mask = self.__get_block_level_mask(
            data=data_norm,
            sparse_block_shape=sparse_block_shape,
            zeros_per_block=zeros_per_block,
        )

        # zero out the entries inside those blocks whose block is sparsified
        mask.data = torch.where(data_lvl_mask == 1, data_lvl_mask, block_lvl_mask)