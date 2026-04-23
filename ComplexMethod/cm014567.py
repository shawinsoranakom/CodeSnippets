def __call__(self, g: NativeFunctionsViewGroup) -> str | None:
        if g.view_copy is None:
            return None
        elif g.view_copy.func.name.name.base != f"{g.view.func.name.name}_copy":
            # If the view_copy doesn't match the standard naming scheme of <op>_copy,
            # assume it already exists and doesn't need to be generated.
            # Example: slice_inverse() with the copy variant named slice_scatter()
            # instead of slice_inverse_copy()
            return None

        metadata = self.backend_index.get_kernel(g.view_copy)
        if metadata is None:
            raise AssertionError(
                f"Expected metadata for view_copy kernel: {g.view_copy}"
            )

        # We can make view_copy work in more cases by using reshape()
        # when a normal view call would ordinarily fail.
        # This also makes LTC more efficient, because they don't need to include
        # clone() calls in their graph (which is normally needed by reshape).
        if str(g.view_copy.func.name) == "view_copy":
            if metadata.kernel != "view_copy_symint":
                raise AssertionError(
                    f"Expected kernel 'view_copy_symint', got '{metadata.kernel}'"
                )
            return """\
at::Tensor view_copy_symint(const at::Tensor & self, at::SymIntArrayRef size) {
  c10::SymDimVector shape = infer_size_dv(size, self.sym_numel());
  if (!at::detail::computeStride(self.sym_sizes(), self.sym_strides(), shape).has_value()) {
    return self.reshape_symint(size);
  } else {
    auto output = at::_ops::view::call(self, size);
    return output.clone(/*memory_format=*/at::MemoryFormat::Contiguous);
  }
}
"""
        # view_copy is a native signature, since we're generating an at::native:: kernel
        # Functionalization always operates on symints though
        view_copy_sig = NativeSignature(
            g.view_copy.func, symint=metadata.supports_symint()
        )

        # view is a dispatcher signature, since we're calling into the at::_ops API
        view_sig = DispatcherSignature(g.view.func)

        view_api_name = g.view.func.name.unambiguous_name()
        exprs = ", ".join(
            [e.expr for e in translate(view_copy_sig.arguments(), view_sig.arguments())]
        )

        # view ops today always return either a Tensor or a list of Tensors
        if len(g.view.func.returns) != 1:
            raise AssertionError(f"Expected 1 return, got {len(g.view.func.returns)}")
        if not (
            g.view.func.returns[0].type == BaseType(BaseTy.Tensor)
            or g.view.func.returns[0].type == ListType(BaseType(BaseTy.Tensor), None)
        ):
            raise AssertionError(
                f"Expected Tensor or Tensor[] return type, got {g.view.func.returns[0].type}"
            )

        if g.view.func.returns[0].type == BaseType(BaseTy.Tensor):
            return_cloned_output = """\
  return output.clone(/*memory_format=*/at::MemoryFormat::Contiguous);"""
        else:
            # If the return type is a list, we need to clone each tensor in the list.
            return_cloned_output = f"""\
  {view_copy_sig.returns_type().cpp_type()} out_clone;
  for (const auto i : c10::irange(output.size())) {{
    out_clone.push_back(output[i].clone(/*memory_format=*/at::MemoryFormat::Contiguous));
  }}
  return out_clone;"""

        # The default generated composite kernel for {view}_copy() operators just clones
        # the input tensor, and runs the underlying view on the clone.
        return f"""
{view_copy_sig.defn(name=metadata.kernel)} {{
  auto output = at::_ops::{view_api_name}::call({exprs});
  {return_cloned_output}
}}
"""