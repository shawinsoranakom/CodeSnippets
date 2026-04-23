def reconstruct(self, codegen: "PyCodegen") -> None:
        codegen.add_push_null(
            lambda: codegen.load_import_from(__name__, "_create_nested_fn")
        )
        codegen(self.code)
        codegen.extend_output([codegen.create_load_const_unchecked(self.f_globals)])
        codegen(ConstantVariable.create(self.code.value.co_name))  # type: ignore[attr-defined]

        if self.defaults:
            codegen(self.defaults)
        else:
            codegen.extend_output([codegen.create_load_const(None)])

        if self.closure:
            codegen(self.closure)
        else:
            codegen.extend_output([codegen.create_load_const(None)])

        if self.kwdefaults:
            codegen(self.kwdefaults)
        else:
            codegen.extend_output([codegen.create_load_const(None)])

        if self.dict_vt and self.dict_vt.contains("__annotations__"):
            annotations = self.dict_vt.getitem("__annotations__")
            try:
                annotations = annotations.as_python_constant()
                codegen.extend_output(
                    [codegen.create_load_const_unchecked(annotations)]
                )
            except NotImplementedError:
                codegen(annotations)
        else:
            codegen.extend_output([codegen.create_load_const(None)])

        codegen.extend_output(create_call_function(7, False))

        if self.wrapped_fn:
            codegen.add_push_null(
                lambda: codegen.load_import_from("functools", "wraps")
            )
            codegen(self.wrapped_fn)
            codegen.extend_output(create_call_function(1, False))
            codegen.extend_output(create_rot_n(2))
            codegen.extend_output(create_call_function(1, True))

        # codegen attributes
        tx = codegen.tx
        if tx.output.side_effects.has_pending_mutation(self):
            for name, value in tx.output.side_effects.store_attr_mutations[
                self
            ].items():
                codegen.dup_top()
                codegen(value)
                codegen.extend_output(create_rot_n(2))
                codegen.store_attr(name)