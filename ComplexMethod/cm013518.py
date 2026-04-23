def prettify_results(
        self,
        original_signature: inspect.Signature,
        dynamic_shapes: dict[str, Any] | tuple[Any] | list[Any],
        constraint_violation_error: object,
        forced_specializations: dict[str, str],
    ) -> str:
        """Format a message for constraint violation errors"""
        from torch.export.dynamic_shapes import _get_dim_name_mapping

        if not self._dcp.source_name_to_debug_name:
            # nothing to do
            return ""

        def transform(s: str, inverse: bool = False) -> str:
            for k, v in self._dcp.source_name_to_debug_name.items():
                s = s.replace(k, v) if not inverse else s.replace(v, k)
            return s

        results: defaultdict[str, dict[str, Any]] = defaultdict(dict)
        if dynamic_shapes is None:
            dynamic_shapes = {}

        def flip(op: str) -> str:
            if op == "<=":
                return ">="
            if op == ">=":
                return "<="
            if op == "<":
                return ">"
            if op == ">":
                return "<"
            if op != "==":
                raise AssertionError(f"Expected op to be '==', got {op}")
            return op

        def relation_with_digit(expr: str, op: str, digit: int) -> None:
            if op == "<=":
                results[expr]["max"] = digit
            elif op == "<":
                results[expr]["max"] = digit - 1
            elif op == ">=":
                results[expr]["min"] = digit
            elif op == ">":
                results[expr]["min"] = digit + 1
            else:
                if op != "==":
                    raise AssertionError(f"Expected op to be '==', got {op}")
                results[expr]["eq"] = digit

        # retrieve dynamic shapes
        name_to_dim = _get_dim_name_mapping(dynamic_shapes)

        for s in self._static_results.union(self._dynamic_results):
            t = transform(s)
            if t == s:
                continue
            left, op, right = re.split(r"( == | <= | >= | < | > )", t)
            op = op.strip()
            if op == "==" and left == right:
                continue
            if right.isdigit():
                relation_with_digit(left, op, int(right))
            elif left.isdigit():
                relation_with_digit(right, flip(op), int(left))
            else:
                if op != "==":
                    raise AssertionError(f"Expected op to be '==', got {op} for {t}")
                try:
                    results[left]["eq"] = sympy.sympify(right)
                except TypeError:  # rhs source is not linked to Dim name
                    pass

        # order forced specializations based on name
        forced_specializations = {
            k: forced_specializations[k]
            for k in sorted(
                forced_specializations.keys(),
                key=lambda x: x.split(" = ")[1],
            )
        }

        buf = ""
        if forced_specializations:
            debug_names = set()
            for k in forced_specializations:
                dim = name_to_dim[k.split(" = ")[0]]
                if self._is_derived_dim(dim):
                    debug_names.add(dim.root.__name__)  # type: ignore[attr-defined]
                else:
                    debug_names.add(dim.__name__)

            buf += (
                f"Specializations unexpectedly required ({', '.join(sorted(debug_names))})! "
                'For more information, run with TORCH_LOGS="+dynamic".\n'
            )
            for s, val in forced_specializations.items():
                buf += f"  - solving the guards generated for {s} resulted in a specialized value of {val}.\n"

        self._process_derived_dim_roots(results, name_to_dim)

        dims: list[str] = []
        others: list[str] = []

        # order results by source name
        results2 = {
            k: results[k]
            for k in sorted(
                results.keys(),
                key=lambda x: transform(x, inverse=True),
            )
        }
        for k, c in results2.items():
            if "eq" in c:
                other = c["eq"]
                if isinstance(other, int):
                    others.append(f"{k} = {other}")
                elif _is_supported_equivalence(other):
                    others.append(f"{k} = {other}")
            else:
                min_ = c.get("min", None)
                if min_ == 2:
                    min_ = None
                max_ = c.get("max", None)
                if min_ is not None and max_ is not None:
                    dims.append(f"{k} = Dim('{k}', min={min_}, max={max_})")
                elif min_ is not None:
                    dims.append(f"{k} = Dim('{k}', min={min_})")
                elif max_ is not None:
                    dims.append(f"{k} = Dim('{k}', max={max_})")
                else:
                    dims.append(f"{k} = Dim('{k}')")

        # results2 will get filtered out if no new suggestions,
        # this can happen if guards are too complex.
        # in that case don't suggest fix
        if dims or others:
            buf += "\nSuggested fixes:\n  "
            buf += "\n  ".join(dims + others)

        return buf