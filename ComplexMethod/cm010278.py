def _parse_tensor_dim(tensor, idx, dim) -> None:
        def _create_static_dim(tensor, i, value):
            return _StaticDim(value)

        if isinstance(dim, (int, Dim)):
            if isinstance(dim, int):
                dim = _create_static_dim(tensor, idx, dim)
            constraint = to_constraint(dim, tensor, idx)
            symbols[dim.__name__].append(constraint)
        elif isinstance(dim, _DimHint):
            if dim.type == _DimHintType.AUTO:
                torch._dynamo.maybe_mark_dynamic(tensor, idx)
            elif dim.type == _DimHintType.STATIC:
                torch._dynamo.mark_static(tensor, idx)
            elif dim.type == _DimHintType.DYNAMIC:
                torch._dynamo.mark_dynamic(tensor, idx)
            constraints.append(_RelaxedConstraint(id(tensor), idx))
        elif dim is None:
            torch._dynamo.mark_static(tensor, idx)