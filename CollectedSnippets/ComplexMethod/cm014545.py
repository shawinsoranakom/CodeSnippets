def __call__(self, f: NativeFunction) -> str:
        sig = DispatcherSignature.from_schema(f.func)
        name = f.func.name.unambiguous_name()

        if self.target is Target.DECLARATION:
            # Note [The ATen Operators API]
            # The ATen Operators API lives in the at::_ops namespace, and contains compile-time
            # metadata about each operator + entry points into the Dispatcher.
            # The C++ function, method, and redispatch API's are all implemented as wrappers
            # into various bits of the structs defined here.
            #
            # Important characteristics about the Operators API:
            # (1) It follows the Dispatcher API.
            #     This is kind of necessary to avoid overhead.
            #     For example: if it followed the C++ API, then all of the faithful C++ factory functions
            #     would need to wrap their arguments into TensorOptions only to unwrap them again.
            # (2) Overload names are disambiguated.
            #     This is helpful for pytorch extenders who would like to decltype() an aten operator,
            #     that has overloads, e.g. decltype(at::_ops::mul_Tensor::call)
            # (3) No argument defaulting is allowed.
            #     This is more of an implementation detail to avoid #include cycles,
            #     since TensorBody.h (which defines the Tensor class) needs to include this file.
            # (4) manual_cpp_bindings and faithful names are not included in the API.
            #     This applies to stuff like __dispatch__is_complex(), and add_outf().
            #     These aren't "real aten ops", they're just additional functions provided by the C++ API.
            #     They're implemented as wrappers in Functions.h that call into the actual operators
            #     defined here, i.e. at::_ops::is_complex::call() and at::_ops::add_out::call().
            #     This means that ATEN_OP(is_complex) will not fastpath, and will go through the dispatcher.
            return f"""
struct TORCH_API {name} {{
  using schema = {sig.type()};
  using ptr_schema = schema*;
  // See Note [static constexpr char* members for windows NVCC]
  static constexpr const char* name = "aten::{f.func.name.name}";
  static constexpr const char* overload_name = "{f.func.name.overload_name}";
  static constexpr const char* schema_str = {cpp_string(str(f.func))};
  static {sig.defn(name="call", is_redispatching_fn=False)};
  static {sig.defn(name="redispatch", is_redispatching_fn=True)};
}};"""

        elif self.target is Target.DEFINITION:
            defns = f"""
// aten::{f.func}
static C10_NOINLINE c10::TypedOperatorHandle<{name}::schema> create_{name}_typed_handle() {{
  return c10::Dispatcher::singleton()
      .findSchemaOrThrow({name}::name, {name}::overload_name)
      .typed<{name}::schema>();
}}
"""
            for is_redispatching_fn in [False, True]:
                if is_redispatching_fn:
                    dispatcher_exprs_str = ", ".join(
                        ["dispatchKeySet"] + [a.name for a in sig.arguments()]
                    )
                    method_base = "redispatch"
                else:
                    dispatcher_exprs_str = ", ".join([a.name for a in sig.arguments()])
                    method_base = "call"

                dispatcher_call = method_base
                method_name = f"{name}::{method_base}"

                fn_body = f"""
    static auto op = create_{name}_typed_handle();
    return op.{dispatcher_call}({dispatcher_exprs_str});"""

                if (
                    not is_redispatching_fn
                    and len(self.static_dispatch_backend_indices) > 0
                ):
                    # call() should go through static dispatch
                    fn_body = static_dispatch(
                        sig, f, backend_indices=self.static_dispatch_backend_indices
                    )
                defns += f"""
// aten::{f.func}
{sig.defn(name=method_name, is_redispatching_fn=is_redispatching_fn)} {{
    {fn_body}
}}
"""
            return defns
        else:
            assert_never(self.target)