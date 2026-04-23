def compute_ufunc_cpu_dtype_body(
    g: NativeFunctionsGroup,
    dtype: ScalarType,
    inner_loops: dict[UfuncKey, UfuncSignature],
    parent_ctx: Sequence[Binding],
) -> str:
    if UfuncKey.CPUScalar not in inner_loops:
        raise AssertionError(f"{dtype}, {inner_loops.keys()}")
    if not inner_loops.keys() <= {UfuncKey.CPUScalar, UfuncKey.CPUVector}:
        raise AssertionError(
            f"inner_loops keys must be subset of CPUScalar/CPUVector, got {inner_loops.keys()}"
        )
    scalar_loop = inner_loops[UfuncKey.CPUScalar]
    vec_loop = None
    if UfuncKey.CPUVector in inner_loops:
        vec_loop = inner_loops[UfuncKey.CPUVector]

    # NB: We DON'T use translate here, because translate is
    # incapable of CSE'ing the scalar accesses in case it is also
    # used by Vectorized; also, the unpacking here is very simple
    # and only affects Scalar; everything else is implicitly captured
    # by the lambda

    # Setup scalar in scope
    body = []
    ctx = []
    for b in parent_ctx:
        if isinstance(b.argument, Argument) and b.argument.type != BaseType(
            BaseTy.Scalar
        ):
            continue
        body.append(f"auto _s_{b.name} = {b.name}.to<scalar_t>();")
        ctx.append(Expr(f"_s_{b.name}", NamedCType(b.nctype.name, BaseCType(scalar_t))))
    if vec_loop is not None:
        for b in parent_ctx:
            if isinstance(b.argument, Argument) and b.argument.type != BaseType(
                BaseTy.Scalar
            ):
                continue
            body.append(
                f"auto _v_{b.name} = at::vec::Vectorized<scalar_t>(_s_{b.name});"
            )
            ctx.append(
                Expr(
                    f"_v_{b.name}",
                    NamedCType(b.nctype.name, VectorizedCType(BaseCType(scalar_t))),
                )
            )

    # Setup lambda signature
    # NB: simplified version of ufunctor_arguments
    scalar_bindings = []
    vec_bindings = []
    for a in g.functional.func.arguments.flat_non_out:
        if not a.type.is_tensor_like():
            continue
        if a.type != BaseType(BaseTy.Tensor):
            raise AssertionError(f"Expected Tensor type, got {a.type}")
        scalar_bindings.append(
            Binding(
                name=a.name,
                nctype=NamedCType(a.name, BaseCType(scalar_t)),
                argument=a,
            )
        )
        if vec_loop is not None:
            vec_bindings.append(
                Binding(
                    name=a.name,
                    nctype=NamedCType(a.name, VectorizedCType(BaseCType(scalar_t))),
                    argument=a,
                )
            )

    def with_ctx(b: Sequence[Binding]) -> list[Expr | Binding]:
        r: list[Expr | Binding] = []
        r.extend(ctx)
        r.extend(b)
        return r

    body_str = "\n".join(body)
    if vec_loop is not None:
        return f"""
{body_str}
cpu_kernel_vec(iter,
  [=]({", ".join(b.decl() for b in scalar_bindings)}) {{ return {scalar_loop.call(with_ctx(scalar_bindings))}; }},
  [=]({", ".join(b.decl() for b in vec_bindings)}) {{ return {vec_loop.call(with_ctx(vec_bindings))}; }}
);
"""
    else:
        return f"""
{body_str}
cpu_kernel(iter,
  [=]({", ".join(b.decl() for b in scalar_bindings)}) {{ return {scalar_loop.call(with_ctx(scalar_bindings))}; }}
);
"""