def _reduction_nocache(
        self,
        dtype: torch.dtype,
        src_dtype: torch.dtype,
        reduction_type: ReductionType,
        value: CSEVariable | tuple[CSEVariable, ...],
    ) -> CSEVariable | tuple[CSEVariable, ...]:
        """Codegen a reduction operation.
        Only sum and prod operations are somewhat reasonable optimized"""
        assert self.inside_reduction
        assert not self._load_mask

        def _unwrap_helper(res3: CSEVariable) -> tuple[CSEVariable, ...]:
            # Uwraps vec3 dtype into individual components
            return OpsWrapper._unwrap(
                [CSEVariable(f"{res3}.{t}", res3.bounds, res3.dtype) for t in "xyz"]
            )

        # Establish reduction buffer size and index expression
        reduction_idx = ""
        acc_buf_size = 1
        for rd in self.range_trees:
            if not rd.is_reduction:
                continue
            if reduction_idx:
                reduction_idx += " + "
            reduction_idx += f"{rd.name} * {acc_buf_size}"

            if isinstance(rd.numel, sympy.Integer):
                acc_buf_size *= rd.numel
            else:
                acc_buf_size *= sympy.Symbol(
                    f"{rd.prefix}numel", integer=True, positive=True
                )

        acc_buf_size = sympy.Min(acc_buf_size, self.max_threadgroup_size)
        acc_buf_size_str = self.sexpr(acc_buf_size)
        shmem_buf_size = (
            ceildiv(acc_buf_size, self.simd_group_size)
            if isinstance(acc_buf_size, sympy.Integer)
            else self.simd_group_size
        )

        if reduction_type == "any":
            acc = self._new_idxvar(dtype)
            self.indexing_code.writeline(f"{acc} = false;")
            self.indexing_code.writeline(
                "threadgroup_barrier(metal::mem_flags::mem_threadgroup);"
            )
            self.compute.splice(
                f"""
                if ({value}) {{
                    {acc} = true;
                }}
            """
            )
            self.stores.writeline(
                "threadgroup_barrier(metal::mem_flags::mem_threadgroup);"
            )
            return acc

        self.headers.add("reduction_utils")

        if reduction_type in ["prod", "sum"]:
            acc_dtype = DTYPE_TO_COMPUTATION_DTYPE[src_dtype]
            acc_buf = self._new_idxvar(acc_dtype, shmem_buf_size)
            if not self.multistage_reduction_entry:
                val = value
            else:
                default_val, reduction_op = (
                    (0, "+") if reduction_type == "sum" else (1, "*")
                )
                val = self._new_idxvar(
                    acc_dtype, default_value=default_val, is_threadgroup=False
                )
                self.compute.splice(f"{val} {reduction_op}= {value};")

            return self.cse.generate(
                self.stores,
                f"c10::metal::threadgroup_{reduction_type}({acc_buf}, {val}, {reduction_idx}, {acc_buf_size_str})",
                dtype=DTYPE_TO_COMPUTATION_DTYPE[dtype],
            )
        if reduction_type in ["max", "min"]:
            acc_buf = self._new_idxvar(src_dtype, shmem_buf_size)
            src_metal_type = DTYPE_TO_METAL[src_dtype]
            cast_value = f"static_cast<{src_metal_type}>({value})"
            if not self.multistage_reduction_entry:
                val = cast_value  # type: ignore[assignment]
            else:
                lim_fn = "lowest" if reduction_type.endswith("max") else "max"
                limit_val = f"::metal::numeric_limits<{src_metal_type}>::{lim_fn}()"
                val = self._new_idxvar(
                    src_dtype, default_value=limit_val, is_threadgroup=False
                )
                self.compute.splice(
                    f"{val} = ::c10::metal::{reduction_type}({val}, {cast_value});"
                )
            return self.cse.generate(
                self.stores,
                f"c10::metal::threadgroup_{reduction_type}({acc_buf}, {val}, {reduction_idx}, {acc_buf_size_str})",
                dtype=DTYPE_TO_COMPUTATION_DTYPE[dtype],
            )
        if reduction_type in ["argmin", "argmax"]:
            data_acc_buf = self._new_idxvar(src_dtype, shmem_buf_size)
            idx_acc_buf = self._new_idxvar(dtype, shmem_buf_size)
            src_metal_type = DTYPE_TO_METAL[src_dtype]
            cast_value = f"static_cast<{src_metal_type}>({value})"
            if not self.multistage_reduction_entry:
                val = cast_value  # type: ignore[assignment]
                idx_val = f"static_cast<{DTYPE_TO_METAL[dtype]}>({reduction_idx})"
            else:
                lim_fn = "lowest" if reduction_type.endswith("max") else "max"
                limit_val = f"::metal::numeric_limits<{src_metal_type}>::{lim_fn}()"
                val = self._new_idxvar(
                    src_dtype, default_value=limit_val, is_threadgroup=False
                )
                idx_val = self._new_idxvar(dtype, default_value=0, is_threadgroup=False)  # type: ignore[assignment]
                idx_var = next(
                    t for t in self.range_tree_nodes.values() if t.is_reduction
                )
                cmp_op = ">" if reduction_type == "argmax" else "<"
                nan_suffix = (
                    f" || ::metal::isnan({value}) "
                    if src_dtype.is_floating_point
                    else ""
                )
                self.compute.splice(f"""
                if ({value} {cmp_op} {val}{nan_suffix}) {{
                    {val} = {value};
                    {idx_val} = {idx_var.name};
                }}
                """)
            return self.cse.generate(
                self.stores,
                f"c10::metal::threadgroup_{reduction_type}({data_acc_buf}, {idx_acc_buf}, "
                f"{val}, {idx_val}, {reduction_idx}, {acc_buf_size_str})",
                dtype=dtype,
            )
        if reduction_type == "welford_reduce":
            if not self.multistage_reduction_entry:
                acc_buf = self._new_idxvar(src_dtype, acc_buf_size)
                self.compute.splice(f"{acc_buf}[{reduction_idx}] = {value};")
                wf_res = self.cse.generate(
                    self.compute,
                    f"c10::metal::threadgroup_{reduction_type}({acc_buf}, {acc_buf_size_str})",
                    dtype=torch.float32,
                )
                return _unwrap_helper(wf_res)
            acc_buf = self._new_idxvar("float3", acc_buf_size)
            acc_thread_var = f"{acc_buf}[{reduction_idx}]"
            self.indexing_code.splice(f"{acc_thread_var} = 0.0;")
            self.compute.writeline(
                f"{acc_thread_var} = ::c10::metal::welford_combine({acc_thread_var}, float3({value}, 0.0, 1.0));"
            )
            wf_res = self.cse.generate(
                self.stores,
                f"c10::metal::threadgroup_welford_combine({acc_buf}, {acc_buf_size})",
                dtype=torch.float32,
            )
            return _unwrap_helper(wf_res)
        if reduction_type == "welford_combine":
            assert isinstance(value, tuple), "Input to welford combine must be tuple"
            acc_buf = self._new_idxvar("float3", acc_buf_size)
            acc_thread_var = f"{acc_buf}[{reduction_idx}]"
            inp_value = f"float3({value[0]}, {value[1]}, {value[2]})"
            self.indexing_code.splice(f"{acc_thread_var} = 0.0;")
            if self.multistage_reduction_entry:
                self.indexing_code.splice(f"{acc_thread_var} = 0.0;")
                self.compute.writeline(
                    f"{acc_thread_var} = ::c10::metal::welford_combine({acc_thread_var}, {inp_value});"
                )
            else:
                self.compute.writeline(f"{acc_thread_var} = {inp_value};")
            wf_res = self.cse.generate(
                self.stores if self.multistage_reduction_entry else self.compute,
                f"c10::metal::threadgroup_{reduction_type}({acc_buf}, {acc_buf_size_str})",
                dtype=torch.float32,
            )
            return _unwrap_helper(wf_res)
        raise NotImplementedError(reduction_type)