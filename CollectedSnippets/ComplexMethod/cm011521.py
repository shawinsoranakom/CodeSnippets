def parse_dims(cls, input_dims: list[str], output_dim: str) -> "EinsumDims":
        """
        Parse the dims and extract the contracting, batch, and free dimensions
        for the left and right hand sides.
        """
        dim_char_set: set[str] = set()
        for input_dim in input_dims:
            dim_char_set.update(input_dim)

        # get a deterministic order of all dim chars
        all_dim_chars = sorted(dim_char_set)

        # parse input and output dimensions
        lhs_out_only_dims, rhs_out_only_dims = [], []
        batch_dims, contracting_dims = [], []

        for dim_char in all_dim_chars:
            if dim_char not in output_dim:
                contracting_dims.append(dim_char)
            else:
                is_batch_dim = True
                for input_dim in input_dims:
                    is_batch_dim = is_batch_dim and dim_char in input_dim

                if is_batch_dim:
                    batch_dims.append(dim_char)
                else:
                    if len(input_dims) != 2:
                        raise AssertionError(
                            "free dimension only supported for two inputs!"
                        )
                    lhs, rhs = input_dims
                    if dim_char in lhs:
                        lhs_out_only_dims.append(dim_char)
                    elif dim_char in rhs:
                        rhs_out_only_dims.append(dim_char)
                    else:
                        raise RuntimeError("Invalid dimension character")

        return cls(
            contracting_dims=contracting_dims,
            batch_dims=batch_dims,
            lhs_out_only_dims=lhs_out_only_dims,
            rhs_out_only_dims=rhs_out_only_dims,
        )