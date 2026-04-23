def gen_transposed_tile_load_store(
        self, name, var, index, is_store, store_mode=None
    ):
        # transposed tile load/store outside the kernel inner loop
        dtype = V.graph.get_dtype(name)
        factor = self.tiling_factor
        src = f"{var} + {cexpr_index(index)}"
        dst = "__place_holder__"
        ld_src = f"{cexpr_index(stride_at_vec_range(index, self.itervars[self.tiling_idx], self.tiling_factor))}"
        ld_dst = f"{cexpr_index(self.num_elems)}"
        if is_store:
            src, dst = dst, src
            ld_src, ld_dst = ld_dst, ld_src

        need_define = True
        if self.inner_is_tiling_idx ^ is_store:
            M, N = self.inner_num_elems, self.outer_num_elems
        else:
            M, N = (
                self.outer_num_elems,
                self.inner_num_elems,
            )
        atomic_add = "true" if (is_store and (store_mode == "atomic_add")) else "false"
        if (isinstance(M, sympy.Expr) and not M.is_number) or (
            isinstance(N, sympy.Expr) and not N.is_number
        ):
            load_or_store = (
                f"transpose_mxn<{DTYPE_TO_CPP[dtype]},{atomic_add}>"
                f"({src}, {ld_src}, {dst}, {ld_dst}, {cexpr_index(M)}, {cexpr_index(N)});"
            )
        else:
            load_or_store = (
                f"transpose_mxn<{DTYPE_TO_CPP[dtype]},{cexpr_index(M)},{cexpr_index(N)},{atomic_add}>"
                f"({src}, {ld_src}, {dst}, {ld_dst});"
            )
        if is_store:
            tile_var = self.cse.newvar()
        elif not self.cse.contains(load_or_store):
            tile_var = self.cse.generate(self.preloads, load_or_store, write=False)
        else:
            need_define = False
            tile_var = self.cse.get(load_or_store)

        if need_define:
            cpp_dtype = DTYPE_TO_CPP[dtype]
            # tiling_factor might be smaller than the alignment of cpp_dtype, such as
            # with a vector that only holds 4 elements due to NEON 128-bit vectors and
            # cpp_dtype being a 64-bit integer.
            alignas = f"alignas(std::max(std::size_t({factor}), alignof({cpp_dtype})))"
            define_line = f"{alignas} {cpp_dtype} {tile_var}[{factor}*{factor}];"
            self.preloads.writeline(define_line)

        load_or_store = load_or_store.replace("__place_holder__", str(tile_var))
        if is_store:
            self.poststores.writeline(DeferredLine(name, load_or_store))
        else:
            self.preloads.writeline(load_or_store)

        return tile_var