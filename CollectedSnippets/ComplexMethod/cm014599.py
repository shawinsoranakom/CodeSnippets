def compute_ufunc_cuda_functors(
    g: NativeFunctionsGroup,
) -> tuple[dict[ScalarType, dict[UfuncKey, UfunctorSignature]], str]:
    # First, build the functors.
    ufunctor_sigs: dict[ScalarType, dict[UfuncKey, UfunctorSignature]] = {}
    ufunctors: list[str] = []
    loops = g.out.ufunc_inner_loop
    scalar_tensor_idx_lookup = {
        UfuncKey.CUDAFunctorOnSelf: 1,
        UfuncKey.CUDAFunctorOnOther: 0,
        UfuncKey.CUDAFunctor: None,
    }
    if eligible_for_binary_scalar_specialization(g):
        keys = [
            UfuncKey.CUDAFunctorOnSelf,
            UfuncKey.CUDAFunctorOnOther,
            UfuncKey.CUDAFunctor,
        ]
    else:
        keys = [UfuncKey.CUDAFunctor]
        for k in [UfuncKey.CUDAFunctorOnSelf, UfuncKey.CUDAFunctorOnOther]:
            if k in loops:
                raise AssertionError(f"cannot use {k} on non-binary function")
    for k in keys:
        # If the key was directly defined, skip functor codegen; we assume the
        # user already done it for us
        if k in loops:
            ufunctor_sig = UfunctorSignature(
                g, scalar_tensor_idx=scalar_tensor_idx_lookup[k], name=loops[k].name
            )
            for dtype in loops[k].supported_dtypes:
                ufunctor_sigs.setdefault(dtype, {})[k] = ufunctor_sig
            continue

        # Note [ScalarOnly and Generic must match names for CUDA]
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Otherwise, look in ANY of the generic entries.  For simplicity of
        # codegen, both ScalarOnly and Generic are defined, the ufunc name
        # must match  (if they didn't match, we'd have to generate distinct
        # functors per dtype, which is awful, so we're not going to do it unless
        # someone really forces us to)
        ufunc_name = None
        supported_dtypes: OrderedSet[ScalarType] = OrderedSet()
        for lk in [UfuncKey.ScalarOnly, UfuncKey.Generic]:
            if lk not in loops:
                continue
            if ufunc_name is None:
                ufunc_name = loops[lk].name
            else:
                # See Note [ScalarOnly and Generic must match names for CUDA]
                if ufunc_name != loops[lk].name:
                    raise AssertionError(
                        "ScalarOnly and Generic must have same ufunc name"
                    )
            supported_dtypes |= loops[lk].supported_dtypes
        if ufunc_name is None:
            raise AssertionError("ufunc_name must be non-None")

        name = f"{k}_{ufunc_name}"
        ufunctor_sig = UfunctorSignature(
            g, scalar_tensor_idx=scalar_tensor_idx_lookup[k], name=name
        )
        for dtype in supported_dtypes:
            ufunctor_sigs.setdefault(dtype, {})[k] = ufunctor_sig

        ufunc_sig = UfuncSignature(
            g, name=f"ufunc::{ufunc_name}", compute_t=BaseCType(opmath_t)
        )
        apply_ctx = ufunctor_sig.fields() + ufunctor_sig.arguments().apply
        ufunctors.append(
            f"""
template <typename scalar_t>
struct {ufunctor_sig.name} {{
  using opmath_t = at::opmath_type<scalar_t>;
  {ufunctor_sig.decl_fields()}
  {ufunctor_sig.inline_defn_ctor()}
  __device__ {ufunctor_sig.decl_apply()} {{
    return {ufunc_sig.call(apply_ctx)};
  }}
}};
"""
        )

    return ufunctor_sigs, "\n".join(ufunctors)