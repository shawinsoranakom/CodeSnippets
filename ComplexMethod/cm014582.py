def __post_init__(self) -> None:
        if not self.view.is_view_op:
            raise AssertionError(f"view is not a view op: {self.view.func.name}")
        if self.view_copy is None:
            if gets_generated_view_copy(self.view):
                raise AssertionError(
                    f"{str(self.view.func.name)} appears to be a new operator that aliases its inputs."
                    " The codegen expects you to add a corresponding operator to native_functions.yaml:"
                    f" {get_view_copy_name(self.view)!s}."
                    " See Note [view_copy NativeFunctions] for details."
                )
        else:
            if not self.view_copy.func.name.name.base.endswith(("_copy", "_scatter")):
                raise AssertionError(
                    f"view_copy name must end with '_copy' or '_scatter': {self.view_copy.func.name}"
                )
            if self.view.func.signature() != self.view_copy.func.signature(
                strip_view_copy_name=True,
            ):
                view_sig = self.view.func.signature()
                view_copy_sig = self.view_copy.func.signature(strip_view_copy_name=True)
                raise AssertionError(
                    f"view and view_copy signatures don't match: {view_sig} != {view_copy_sig}"
                )
            if "view_copy" not in self.view_copy.tags:
                raise AssertionError(
                    f"{str(self.view_copy.func.name), str(self.view.tags)} appears to be a view_copy operator. The codegen expects"
                    " view_copy operators to be annotated with the 'view_copy' tag in native_functions.yaml."
                    " See Note [view_copy NativeFunction] for details."
                )
        if self.view_inplace is not None:
            if self.view.func.signature() != self.view_inplace.func.signature():
                view_sig = self.view.func.signature()
                view_inplace_sig = self.view_inplace.func.signature()
                raise AssertionError(
                    f"view and view_inplace signatures don't match: {view_sig} != {view_inplace_sig}"
                )

        if self.view.has_composite_implicit_autograd_kernel:
            if self.view_inplace is not None:
                if not self.view_inplace.has_composite_implicit_autograd_kernel:
                    raise AssertionError(
                        f"{str(self.view.func.name)} and {str(self.view_inplace.func.name)} must either"
                        " both have CompositeImplicitAutograd kernels, or both not have composite kernels."
                    )
        if self.view.has_composite_implicit_autograd_nested_tensor_kernel:
            if self.view_inplace is not None:
                if not self.view_inplace.has_composite_implicit_autograd_nested_tensor_kernel:
                    raise AssertionError(
                        f"{str(self.view.func.name)} and {str(self.view_inplace.func.name)} must either"
                        " both have CompositeImplicitAutogradNestedTensor kernels, or both not have composite kernels."
                    )