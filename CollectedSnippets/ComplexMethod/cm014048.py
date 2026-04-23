def codegen_save_tempvars(self, cg: PyCodegen) -> None:
        # We must codegen modified VT to their source by default, so that
        # mutation and aliasing are properly accounted for.
        #
        # Since newly constructed objects don't have a source, we manually
        # codegen their construction and store them to a newly assigned local
        # source. Note that `ValueMutationNew` isn't tracked by SideEffects.
        for var in self._get_modified_vars():
            if not isinstance(var.mutation_type, AttributeMutationNew):
                assert var.source is not None
                continue

            # Namedtuples/structseqs with no pending mutations should skip
            # codegen_save_tempvars so that restore_stack handles them. In
            # export, restore_stack uses value_from_source=False which makes
            # child tensors become graph outputs. If we processed them here,
            # add_cache would assign a TempLocalSource and restore_stack would
            # load from cache with value_from_source=True, hiding the tensors
            # from export.
            if isinstance(
                var,
                (variables.NamedTupleVariable, variables.StructSequenceVariable),
            ) and not self.has_pending_mutation(var):
                continue

            if isinstance(var, variables.CellVariable):
                # Cells created in the root frame are created either by
                # `MAKE_CELL` or by them being in `co_cellvars`, so we only emit
                # `make_cell` for the non-root-frame cells here.
                # TODO generalize this so we never need to call `make_cell`.
                if var.local_name is None:
                    cg.add_push_null(
                        lambda: cg.load_import_from(utils.__name__, "make_cell")
                    )
                    cg.extend_output(create_call_function(0, False))
                    cg.add_cache(var)
                    var.source = TempLocalSource(cg.tempvars[var])  # type: ignore[attr-defined]
                elif var.source is None:
                    var.source = LocalCellSource(var.local_name)
            elif var.is_tensor():
                # NOTE: for historical reasons we never assigned local sources
                # to newly constructed tensor object, so we keep it that way.
                # They are always loaded from output of the fx graph, so one can
                # think of it as having a "OutputGraphSource" for codegen
                # purposes.
                #
                # However, tensor subclass objects are different, because the
                # reconstruction logic in `PyCodegen` loads the data tensor from
                # graph output and then calls `as_subclass`, meaning we must
                # assign a source to it to ensure we only reconstruct one
                # subclass instance.
                if isinstance(
                    var, variables.torch_function.TensorWithTFOverrideVariable
                ):
                    # Don't codegen from temp source assigned from the 1st pass.
                    cg(var, allow_cache=False)
                    cg.add_cache(var)
                    # `add_cache` generates STORE and consumes TOS, but we never
                    # cleared it. TODO move this call into `add_cache`
                    cg.clear_tos()
                    var.source = TempLocalSource(cg.tempvars[var])
            elif isinstance(var, variables.AutogradFunctionContextVariable):
                unimplemented(
                    gb_type="AutogradFunctionContextVariable escaped Dynamo-traced region",
                    context="",
                    explanation="We cannot reconstruct a torch.autograd.Function's context object.",
                    hints=[],
                )
            else:
                # Reconstruct the bytecode for
                # base_cls.__new__(user_cls, *args)
                if isinstance(var, variables.UserDefinedObjectVariable):

                    def load_new_method() -> None:
                        # pyrefly: ignore [missing-attribute]
                        assert var.base_cls_vt is not None
                        cg(var.base_cls_vt)  # type: ignore[attr-defined]
                        cg.extend_output([cg.create_load_attr("__new__")])

                    cg.add_push_null(load_new_method)
                else:
                    cg.add_push_null(
                        lambda: cg.load_import_from(utils.__name__, "object_new")
                    )
                assert var.mutation_type.cls_source is not None
                cg(var.mutation_type.cls_source)

                # Generate the args to the __new__ method
                for arg in var.init_args:  # type: ignore[attr-defined]
                    cg(arg)

                # Call the __new__ method
                cg.extend_output(create_call_function(1 + len(var.init_args), False))  # type: ignore[attr-defined]

                cg.add_cache(var)
                var.source = TempLocalSource(cg.tempvars[var])

                # For frozen dataclasses, we must emit object.__setattr__
                # immediately after __new__ — before any other code can
                # access the object.  The suffix-based codegen in
                # codegen_update_mutated runs too late: if intervening code
                # calls __repr__ (e.g. f-strings), the attributes won't be
                # set yet.
                if (
                    isinstance(var, variables.FrozenDataClassVariable)
                    and var in self.store_attr_mutations
                ):
                    for name, value in self.store_attr_mutations[var].items():
                        cg.load_import_from("builtins", "object")
                        cg.load_method("__setattr__")
                        cg(var.source)
                        cg(variables.ConstantVariable(name))
                        cg(value)
                        cg.extend_output(
                            [*create_call_method(3), create_instruction("POP_TOP")]
                        )

        for ctx, args in self.save_for_backward:
            cg(ctx.source)
            cg.load_method("save_for_backward")
            for arg in args:
                cg(arg)
            cg.extend_output(
                [
                    *create_call_method(len(args)),
                    create_instruction("POP_TOP"),
                ]
            )