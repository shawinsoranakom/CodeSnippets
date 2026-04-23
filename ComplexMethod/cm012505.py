def _get_reduction_axes(self) -> tuple[int, ...]:
        """Determine which axes of the loaded array are reduction axes.

        Finds the innermost reduction stride from the load index
        expression, then walks outward through the buffer's dims
        using stride ratios until the accumulated product reaches
        red_numel.  Falls back to stride-direction analysis for
        gather/flatten loads.
        """
        if not self.load_index_exprs:
            return (-1,)

        r_vars = [v for v, e in self.range_tree_nodes.items() if e.is_reduction]
        pw_vars = [v for v, e in self.range_tree_nodes.items() if not e.is_reduction]
        if not r_vars or not pw_vars:
            return (-1,)

        red_numel = self._compute_reduction_numel()
        if not red_numel or red_numel <= 1:
            return (-1,)

        for buf_name, load_index in self.load_index_exprs.items():
            info = self._get_buffer_info(buf_name)
            if info is None:
                continue
            _, buf_size, _, actual_strides, _ = info
            nd = len(buf_size)
            if nd < 2:
                continue
            strides_or_none = [self._safe_int(s) for s in actual_strides]
            if any(s is None for s in strides_or_none):
                continue
            strides: list[int] = cast(list[int], strides_or_none)

            # Get reduction stride coefficients by zeroing pw_vars.
            r_only = load_index
            for pv in pw_vars:
                r_only = r_only.subs(pv, 0)
            r_coeffs: OrderedSet[int] = OrderedSet()
            for term in sympy.Add.make_args(r_only):
                if term.is_number:
                    continue
                coeff, _ = term.as_coeff_Mul()
                c = self._safe_int(coeff)
                if c is not None and c > 0:
                    r_coeffs.add(c)
            if not r_coeffs:
                continue

            # Match all coefficients against buffer strides
            matched = sorted(
                (i for i in range(nd) if strides[i] in r_coeffs),
            )
            if not matched:
                continue

            # Multiple r_vars each map to a distinct dim — return directly.
            # Single r_var with multiple coefficients (transposed access)
            # → skip to fallback.
            if len(r_coeffs) > 1:
                if len(r_coeffs) == len(matched) and len(r_vars) > 1:
                    return tuple(i - nd for i in matched)
                continue

            # Single coefficient: walk outward from the matched dim
            # using span to find flattened contiguous dims.
            r_stride = next(iter(r_coeffs))
            span = (red_numel - 1) * r_stride
            is_contiguous = all(strides[i] > strides[i + 1] for i in range(nd - 1))
            if is_contiguous:
                # Walk by dim index (strides are in descending order)
                inner = matched[-1]
                start = inner
                while start > 0 and span > strides[start - 1]:
                    start -= 1
                axes = list(range(start, inner + 1))
            else:
                # Non-contiguous layout: collect dims whose strides
                # fall within the r_var's traversal range
                axes = sorted(
                    i
                    for i in range(nd)
                    if r_stride <= strides[i] and strides[i] < span + r_stride
                )
                if not axes:
                    axes = list(matched)
            return tuple(i - nd for i in axes)

        # Fallback: stride-direction for gather/flatten loads
        load_index = next(iter(self.load_index_exprs.values()))
        r_coeff = load_index.coeff(r_vars[0])
        r_stride = self._safe_int(r_coeff) if r_coeff != 0 else 1
        if r_stride is None:
            r_stride = 1
        pw_coeff = load_index.coeff(pw_vars[0])
        pw_stride = self._safe_int(pw_coeff) if pw_coeff != 0 else 1
        if pw_stride is None:
            pw_stride = 1
        if r_stride > pw_stride:
            return (0,)
        return (-1,)