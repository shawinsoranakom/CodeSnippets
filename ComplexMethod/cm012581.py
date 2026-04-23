def get_block_shape(cls, expr: sympy.Expr) -> BlockShapeType:
        # return block shape of sympy Expression
        # e.g.,
        # tmp13 = y1
        # tmp14 = x0 - tmp13
        #
        # get_block_shape(y1) = (YBLOCK,1,1)
        # get_block_shape(x0-tmp13) = (YBLOCK,XBLOCK,1)

        expr_shape: BlockShapeType = ()
        expr_vars = expr.free_symbols
        for var in expr_vars:
            if symbol_is_type(var, SymT.TMP):
                cse_var = V.kernel.cse.varname_map[var.name]
                var_shape = cse_var.shape
            elif symbol_is_type(
                var,
                (
                    SymT.UNBACKED_INT,
                    SymT.SIZE,
                    SymT.PRECOMPUTED_SIZE,
                    SymT.INDEX,
                    SymT.FLOAT,
                    SymT.UNBACKED_FLOAT,
                ),
            ):
                var_shape = ()
            else:
                symbol_matches = [
                    symt for symt in cls.block_types if symbol_is_type(var, symt)
                ]
                assert len(symbol_matches) == 1, f"Ambiguous type: {var.name}"

                sym = symbol_matches[0]
                ndim = V.kernel.triton_tensor_ndim()
                shape = ["1"] * ndim

                tree_match = [
                    tree
                    for tree in V.kernel.active_range_trees()
                    if prefix_str[sym] == tree.prefix
                ]
                assert len(tree_match) == 1, "# of Match expected to 1"

                if tree_match[0].tensor_dim is None:
                    # tree has no tensor dimension (e.g. no_x_dim mode),
                    # treat as scalar
                    var_shape = ()
                else:
                    shape[tree_match[0].tensor_dim] = str(
                        cls.get_block_size(tree_match[0])
                    )
                    var_shape = tuple(shape)

            # Union current variable shape
            expr_shape = get_broadcasted_shape(expr_shape, var_shape)

        assert expr_shape is not None

        return expr_shape