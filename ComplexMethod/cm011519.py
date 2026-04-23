def linalg_batch_dim_strategy(
    op: torch._ops.OpOverload,
    args_schema: tuple[Any, ...],
    kwargs_schema: dict[str, Any],
) -> list[list[Placement | _ShardingPlaceholder]]:
    ndim = _get_ndim(args_schema[0])
    if op not in _LINALG_NUM_PLACEMENTS:
        raise AssertionError(f"Expected op in _LINALG_NUM_PLACEMENTS, got {op}")

    n_placements = _LINALG_NUM_PLACEMENTS[op]
    strategies = _linalg_batch_dim_strategies(ndim, n_placements=n_placements)

    if op == aten.linalg_solve_triangular.default:
        # solve_triangular(A, B) -> result: linear in B
        strategies.append([Partial(), Replicate(), Partial()])
        strategies.append([Partial("avg"), Replicate(), Partial("avg")])
        # A replicated, B sharded on batch dims (B may have more batch dims than A)
        ndim_b = _get_ndim(args_schema[1])
        for dim in range(ndim_b - 2):
            strategies.append(
                [_ShardingPlaceholder(dim), Replicate(), _ShardingPlaceholder(dim)]
            )
    elif op == aten.cholesky_solve.default:
        # cholesky_solve(B, A) -> result  (B is arg0)
        strategies.append([Partial(), Partial(), Replicate()])
    elif op == aten.linalg_lu_solve.default:
        # linalg_lu_solve(LU, pivots, B) -> result
        strategies.append([Partial(), Replicate(), Replicate(), Partial()])
    elif op == aten.linalg_ldl_solve.default:
        # linalg_ldl_solve(LD, pivots, B) -> result
        strategies.append([Partial(), Replicate(), Replicate(), Partial()])
    elif op == aten.ormqr.default:
        # ormqr(a, tau, C) -> result  (linear in C)
        strategies.append([Partial(), Replicate(), Replicate(), Partial()])
    elif op == aten._linalg_solve_ex.default:
        # _linalg_solve_ex(A, B) -> (result, LU, pivots, info)
        strategies.append(
            [Partial(), Replicate(), Replicate(), Replicate(), Replicate(), Partial()]
        )

    return strategies