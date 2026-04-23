def replace_opcode_if_evaluates_pure(
        self,
        tkn: Token,
        tkn_iter: TokenIterator,
        uop: CodeSection,
        storage: Storage,
        inst: Instruction | None,
    ) -> bool:
        assert isinstance(uop, Uop)
        input_identifiers = []
        for token in tkn_iter:
            if token.kind == "IDENTIFIER":
                input_identifiers.append(token)
            if token.kind == "SEMI":
                break

        output_identifier = input_identifiers.pop()

        if len(input_identifiers) == 0:
            raise analysis_error(
                "To evaluate an operation as pure, it must have at least 1 input",
                tkn
            )
        # Check that the input identifiers belong to the uop's
        # input stack effect
        uop_stack_effect_input_identifers = {inp.name for inp in uop.stack.inputs}
        for input_tkn in input_identifiers:
            if input_tkn.text not in uop_stack_effect_input_identifers:
                raise analysis_error(f"{input_tkn.text} referenced in "
                                     f"REPLACE_OPCODE_IF_EVALUATES_PURE but does not "
                                     f"exist in the base uop's input stack effects",
                                     input_tkn)
        input_identifiers_as_str = {tkn.text for tkn in input_identifiers}
        used_stack_inputs = [inp for inp in uop.stack.inputs if inp.name in input_identifiers_as_str]
        assert len(used_stack_inputs) > 0
        self.out.start_line()
        emitter = OptimizerConstantEmitter(self.out, {}, self.original_uop, self.stack.copy())
        emitter.emit("if (\n")
        for inp in used_stack_inputs[:-1]:
            emitter.emit(f"sym_is_safe_const(ctx, {inp.name}) &&\n")
        emitter.emit(f"sym_is_safe_const(ctx, {used_stack_inputs[-1].name})\n")
        emitter.emit(') {\n')
        # Declare variables, before they are shadowed.
        for inp in used_stack_inputs:
            if inp.used:
                emitter.emit(f"{type_name(inp)}{inp.name}_sym = {inp.name};\n")
        # Shadow the symbolic variables with stackrefs.
        for inp in used_stack_inputs:
            if inp.is_array():
                raise analysis_error("Pure evaluation cannot take array-like inputs.", tkn)
            if inp.used:
                emitter.emit(f"{stackref_type_name(inp)}{inp.name} = sym_get_const_as_stackref(ctx, {inp.name}_sym);\n")
        # Rename all output variables to stackref variant.
        for outp in self.original_uop.stack.outputs:
            if outp.is_array():
                raise analysis_error(
                    "Array output StackRefs not supported for evaluating pure ops.",
                    self.original_uop.body.open
                )
            emitter.emit(f"_PyStackRef {outp.name}_stackref;\n")


        storage = Storage.for_uop(self.stack, self.original_uop, CWriter.null(), check_liveness=False)
        # No reference management of outputs needed.
        for var in storage.outputs:
            var.in_local = True
        emitter.emit("/* Start of uop copied from bytecodes for constant evaluation */\n")
        emitter.emit_tokens(self.original_uop, storage, inst=None, emit_braces=False)
        self.out.start_line()
        emitter.emit("/* End of uop copied from bytecodes for constant evaluation */\n")
        for outp in self.original_uop.stack.outputs:
            if not outp.name == output_identifier.text:
                emitter.emit(f"(void){outp.name}_stackref;\n")

        # Output stackref is created from new reference.
        emitter.emit(f"{output_identifier.text} = sym_new_const_steal(ctx, PyStackRef_AsPyObjectSteal({output_identifier.text}_stackref));\n")

        if self.original_uop.name.startswith('_'):
            # Map input count to output index (from TOS) and the appropriate constant-loading uop
            input_count_to_uop = {
                1: {
                    # (a -- res), usually for unary ops
                    0: [("_POP_TOP", "0, 0"),
                        ("_LOAD_CONST_INLINE_BORROW",
                         "0, (uintptr_t)result")],
                    # (left -- res, left)
                    # usually for unary ops with passthrough references
                    1: [("_LOAD_CONST_INLINE_BORROW",
                         "0, (uintptr_t)result"),
                        ("_SWAP", "2, 0")],
                },
                2: {
                    # (a, b -- res), usually for binary ops
                    0: [("_POP_TOP", "0, 0"),
                        ("_POP_TOP", "0, 0"),
                        ("_LOAD_CONST_INLINE_BORROW",
                         "0, (uintptr_t)result")],
                    # (left, right -- res, left, right)
                    # usually for binary ops with passthrough references
                    2: [("_LOAD_CONST_INLINE_BORROW",
                         "0, (uintptr_t)result"),
                        ("_SWAP", "3, 0"),
                        ("_SWAP", "2, 0")],
                },
            }

            output_index = -1
            for idx, outp in enumerate(reversed(uop.stack.outputs)):
                if outp.name == output_identifier.text:
                    output_index =  idx
                    break
            else:
                raise analysis_error(f"Could not find output {output_identifier.text} in uop.", output_identifier)
            assert output_index >= 0
            input_count = len(used_stack_inputs)
            if input_count in input_count_to_uop and output_index in input_count_to_uop[input_count]:
                ops = input_count_to_uop[input_count][output_index]
                input_desc = "one input" if input_count == 1 else "two inputs"
                ops_desc = " + ".join(op for op, _ in ops)

                emitter.emit(f"if (sym_is_const(ctx, {output_identifier.text})) {{\n")
                emitter.emit(f"PyObject *result = sym_get_const(ctx, {output_identifier.text});\n")
                emitter.emit(f"if (_Py_IsImmortal(result)) {{\n")
                emitter.emit(f"// Replace with {ops_desc} since we have {input_desc} and an immortal result\n")
                for op, args in ops:
                    emitter.emit(f"ADD_OP({op}, {args});\n")
                emitter.emit("}\n")
                emitter.emit("}\n")

        storage.flush(self.out)
        emitter.emit("break;\n")
        emitter.emit("}\n")
        return True