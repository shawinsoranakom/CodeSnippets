def _select_tiling_indices(
        self,
        fn_list,
        var_sizes_list,
        tiling_factor,
    ):
        all_index = []
        for fn, var_sizes in zip(fn_list, var_sizes_list):
            rw = dependencies.extract_read_writes(fn, *var_sizes)
            all_index += [dep.index for dep in itertools.chain(rw.reads, rw.writes)]
        contig_vars = OrderedSet[int]()
        contig_vars_list = []
        non_contig_stride_const = OrderedSet[int]()
        non_contig_stride_other = OrderedSet[int]()
        for index in all_index:
            for var in index.free_symbols:
                if not re.search(r"^d\d+$", var.name):
                    continue
                stride = stride_at_vec_range(index, var, tiling_factor)
                if stride == 0:
                    continue
                elif stride == 1:
                    contig_vars.add(int(var.name[1:]))
                    contig_vars_list.append(int(var.name[1:]))
                elif all(symbol_is_type(s, SymT.SIZE) for s in stride.free_symbols):
                    non_contig_stride_const.add(int(var.name[1:]))
                else:
                    non_contig_stride_other.add(int(var.name[1:]))
        contig_only = contig_vars - non_contig_stride_const - non_contig_stride_other
        group, reduction_group = max(var_sizes_list, key=lambda sizes: len(sizes[1]))
        num_itervars = len(group) + len(reduction_group)
        if len(contig_vars) == 0:
            # no contiguous vars
            return [num_itervars - 1]
        if contig_only:
            return sorted(contig_only)[-1:]
        contig_and_const_stride = (
            contig_vars & non_contig_stride_const
        ) - non_contig_stride_other
        contig_vars_sorted = sorted(contig_vars)
        if (
            len(contig_vars_sorted) == 2
            and contig_vars_sorted[-1] in contig_and_const_stride
            and contig_vars_sorted[-1] == num_itervars - 1
        ):
            return contig_vars_sorted
        return sorted(contig_vars_sorted, key=contig_vars_list.count)[-1:]