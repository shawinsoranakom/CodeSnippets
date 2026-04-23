def store(self, name, index, value, mode=None):
        assert "buf" in name
        assert isinstance(value, CppCSEVariable), value
        if not value.is_vec:
            # this happens when we store a scalar into a vectorized buffer like "fill"
            value = self.broadcast(value)
        var = self.args.output(name)
        index = self.rename_indexing(index)
        dtype = V.graph.get_dtype(name)
        if mode is None:
            code = self._get_store_line(value, var, index, dtype)
            self.stores.splice(code.map(lambda x: DeferredLine(name, x)))
        elif mode == "atomic_add":
            if not config.cpp.dynamic_threads and self.num_threads == 1:
                code = self._get_store_line(
                    f"{value}",
                    var,
                    index,
                    dtype,
                    accu_store=True,
                )
                self.stores.splice(code.map(lambda x: DeferredLine(name, x)))
            else:
                n_src = self._get_num_vectors(dtype)
                n_idx = self._get_num_vectors(torch.int64)
                cdtype = DTYPE_TO_CPP[dtype]
                index = ops.index_expr(index, torch.int64).value
                assert isinstance(index, CppCSEVariable) and index.is_vec
                if self.tail_size:
                    line = f"atomic_add_vec<{cdtype}, {n_idx}, {n_src}>({var}, {index}, {value}, {cexpr_index(self.tail_size)});"
                else:
                    line = f"atomic_add_vec<{cdtype}, {n_idx}, {n_src}>({var}, {index}, {value});"
                self.stores.writeline(DeferredLine(name, line))
        else:
            raise NotImplementedError(f"store mode={mode}")