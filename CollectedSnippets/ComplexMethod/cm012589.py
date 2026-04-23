def index_expr(cls, expr, dtype):
        expr = _materialize_trunc_to_float_expr(expr, dtype)
        indexing = V.kernel.indexing(
            expr, block_ptr=False, tma_compatibility_checker=None
        )
        assert isinstance(indexing, IndexingOptions)

        shape: BlockShapeType
        if indexing.expand_shape:
            shape = indexing.expand_shape
        else:
            shape = TritonSymbols.get_block_shape(indexing.index)

        # Our sympy expr printing casts to the current kernel index dtype.
        # we only respect non int32-int64 dtypes and otherwise use current kernel indexing dtype
        index_dtype = V.kernel.get_index_dtype_as_torch_dtype()
        dtype = dtype if dtype not in (torch.int32, torch.int64) else index_dtype

        # after we emit this var we cast it to the correct dtype
        orig = config.test_configs.runtime_triton_dtype_assert
        try:
            config.test_configs.runtime_triton_dtype_assert = False
            var = V.kernel.cse.generate(
                V.kernel.compute,
                indexing.index_str,
                bounds=get_bounds_index_expr(expr),
                dtype=dtype,
                shape=shape,
            )
        finally:
            config.test_configs.runtime_triton_dtype_assert = orig

        if dtype not in (torch.int32, torch.int64):
            var = V.kernel.cse.generate(
                V.kernel.compute,
                cls.to_dtype(var, dtype),
                dtype=upcast_compute_type(dtype),
                shape=var.shape,
            )
        else:
            # TODO: we are not always consistent in enforcing that the output of the index expr printing
            # results in the indexing dtype. So if we detect that we have an input which might type promote
            # to a dtype other than indexing dtype, add a cast.
            # Trying to avoid
            dtype = index_dtype
            for index_var in expr.free_symbols:
                if symbol_is_type(index_var, SymT.TMP):
                    dtype = torch.promote_types(
                        dtype, V.kernel.cse.varname_map[index_var.name].dtype
                    )

            if dtype != index_dtype:
                var = V.kernel.cse.generate(
                    V.kernel.compute,
                    cls.to_dtype(var, index_dtype),
                    dtype=index_dtype,
                    shape=var.shape,
                )

        var.mask_vars = indexing.mask_vars
        return var