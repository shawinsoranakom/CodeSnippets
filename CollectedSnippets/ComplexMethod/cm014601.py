def compute_ufunc_cpu_kernel(g: NativeFunctionsGroup) -> str:
    stub_sig = StubSignature(g)

    # Reindex the ufunc by dtypes; processing generic/scalaronly as well
    loops = g.out.ufunc_inner_loop
    ufunc_sigs: dict[ScalarType, dict[UfuncKey, UfuncSignature]] = {}
    for k in [UfuncKey.CPUScalar, UfuncKey.CPUVector]:
        lks = []
        # ORDER MATTERS: this specifies overriding precedence
        if k in loops:  # should happen rarely
            lks.append(k)
        if UfuncKey.ScalarOnly in loops and k is UfuncKey.CPUScalar:
            lks.append(UfuncKey.ScalarOnly)
        if UfuncKey.Generic in loops:
            lks.append(UfuncKey.Generic)
        # TODO: don't hardcode ufunc:: namespace here, should be centralized smh
        for lk in lks:
            for dtype in loops[lk].supported_dtypes:
                compute_t: CType
                if k is UfuncKey.CPUScalar:
                    compute_t = BaseCType(scalar_t)
                elif k is UfuncKey.CPUVector:
                    compute_t = VectorizedCType(BaseCType(scalar_t))
                else:
                    raise AssertionError
                inner_ufunc_sigs = ufunc_sigs.setdefault(dtype, {})
                if k not in inner_ufunc_sigs:
                    inner_ufunc_sigs[k] = UfuncSignature(
                        g, name=f"ufunc::{loops[lk].name}", compute_t=compute_t
                    )

    # Build the conditionals
    dtype_cases = []
    for dtype, inner_ufunc_sigs in ufunc_sigs.items():
        dtype_cases.append(
            f"""
AT_DISPATCH_CASE(at::ScalarType::{dtype},
  [&]() {{
    {compute_ufunc_cpu_dtype_body(g, dtype, inner_ufunc_sigs, stub_sig.arguments())}
  }}
)
"""
        )

    dtype_cases_str = "\n".join(dtype_cases)
    return f"""
namespace {{

{stub_sig.kernel_defn()} {{
  AT_DISPATCH_SWITCH(iter.common_dtype(), "{stub_sig.name}",
    {dtype_cases_str}
  );
}}

}} // anonymous namespace

{stub_sig.type_defn()};
{stub_sig.dispatch_decl()}
REGISTER_DISPATCH({stub_sig.name}, &{stub_sig.kernel_name})
"""