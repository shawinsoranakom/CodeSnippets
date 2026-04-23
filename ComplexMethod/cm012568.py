def generate(
        self,
        buffer: IndentedBuffer,
        expr: str | CSEVariable | OpsValue | IndentedBuffer | DeferredLineBase,
        *,
        bounds: ValueRanges[Any] = ValueRanges.unknown(),
        write: bool = True,
        assignment: bool = True,
        dtype: torch.dtype | None = None,
        shape: BlockShapeType = None,
    ) -> CSEVariableType:
        if isinstance(expr, OpsValue):
            expr = expr.value

        assert write or assignment
        if isinstance(expr, CSEVariable):
            # If the expressions were always created with all the information, we could
            # assert expr.bounds == bounds, but sometimes the expression is created
            # with the loose ValueRanges.unknown(), so we need to tighten the bounds
            expr.bounds = expr.bounds.tighten(bounds)
            expr.use_count += 1
            return cast(CSEVariableType, expr)
        elif isinstance(expr, IndentedBuffer):
            cache_key = expr.getvalue()
        elif isinstance(expr, DeferredLineBase):
            cache_key = expr.line
        else:
            assert isinstance(expr, str)
            cache_key = expr
        var = self.try_get(cache_key)
        if shape is None and not assignment:
            # since there's no assignment to a variable, use any shape here
            # other than None to avoid the unknown shape failures
            shape = ()
        if not var:
            var = self.newvar(bounds, dtype, shape)
            self.put(cache_key, var)
            if write:
                if V.kernel.current_node:
                    V.kernel.current_node.codegen_originating_info(
                        buffer, only_once=True
                    )
                if isinstance(expr, IndentedBuffer):
                    if assignment:
                        buffer.writeline(f"{self.prefix}{var} =")
                    buffer.splice(expr)
                    buffer.writeline(self.suffix)
                elif isinstance(expr, DeferredLineBase):
                    assert assignment
                    buffer.writeline(
                        expr._new_line(f"{self.prefix}{var} = {expr.line}{self.suffix}")
                    )
                else:
                    if assignment:
                        line = f"{self.prefix}{var} = {expr}{self.suffix}"
                    else:
                        line = f"{expr}{self.suffix}"
                    buffer.writeline(line)

                    # cpp backend cannot determine is_vec at this point
                    if (
                        assignment
                        and (
                            config.test_configs.runtime_triton_dtype_assert
                            or config.test_configs.static_cpp_dtype_assert
                        )
                        and dtype is not None
                        and get_current_backend() != "cpp"
                    ):
                        check_dtype(buffer, var, dtype)

        else:
            var.bounds = var.bounds.tighten(bounds)
            var.use_count += 1

        return var