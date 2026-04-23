def reshape_transpose_broadcast_for_dot(
            value,
            initial_shape: Sequence[sympy.Expr],
            final_shape: Sequence[sympy.Expr],
        ) -> str:
            """
            Generate a reshape, transpose, and broadcast for the tl.dot.
            tl.dot requires specific shape requirement : (Y,R) x (R,X)
            but the current triton codegen eagerly broadcast the tl.arange so
            it needs to be reshaped to meet the requirement.

            This is done by three steps.
            1. remove the empty dimension (dim with size 1) and make it 2d with tl.reshape
            2. permute the dimension if needed (e.g., (X,R) -> (R,X)) with tl.trans
            3. broadcast if needed with broadcast_to.
                - This shows up when matmul operand is broadcasted with torch.expand/repeat.
                - e.g., torch.rand((16,)).expand(16,16) @ B

            e.g., (Y,1,R), (Y,R) -> tl.reshape(var, (Y,R))
            e.g., (1,X,R), (R,X) -> tl.trans(tl.reshape(var, (X,R)))
            e.g., (1,X,1), (R,X) -> tl.broadcast_to(tl.trans(tl.reshape(var, (X,1))), (R,X))

            TODO : eventually we want to remove this function when lazy broadcasting arrives
            """

            # Triton 3d dot is slower than 2d dot, so we want to keep block shape in 2d
            # by fixing ZBLOCK=1 in the autotune config
            if ZBLOCK in initial_shape:
                initial_shape = ["1" if dim == ZBLOCK else dim for dim in initial_shape]

            if final_shape == [YBLOCK, RBLOCK]:
                assert XBLOCK not in initial_shape, (
                    "left tl.dot operand cannot depend on x"
                )

                shape_2d = ["1", "1"]
                if YBLOCK in initial_shape:
                    shape_2d[0] = YBLOCK
                if RBLOCK in initial_shape:
                    shape_2d[1] = RBLOCK

                # reshape it into 2d
                value = triton_reshape(value, initial_shape, shape_2d)

                # broadcast if needed
                broadcast_needed = shape_2d != [YBLOCK, RBLOCK]
                if broadcast_needed:
                    value = f"tl.broadcast_to({value}, ({YBLOCK}, {RBLOCK}))"

            elif final_shape == [RBLOCK, XBLOCK]:
                assert YBLOCK not in initial_shape, (
                    "right tl.dot operand cannot depend on y"
                )

                shape_2d = ["1", "1"]
                if XBLOCK in initial_shape:
                    shape_2d[0] = XBLOCK
                if RBLOCK in initial_shape:
                    shape_2d[1] = RBLOCK

                # reshape it into 2d (X,R)
                value = triton_reshape(value, initial_shape, shape_2d)

                # transpose to (R,X)
                value = f"tl.trans({value})"

                # broadcast if needed
                broadcast_needed = shape_2d != [XBLOCK, RBLOCK]
                if broadcast_needed:
                    value = f"tl.broadcast_to({value}, ({RBLOCK}, {XBLOCK}))"
            else:
                raise NotImplementedError

            return value