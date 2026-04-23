def __call__(
        self, code_options: dict[str, Any], cleanup: list[Instruction]
    ) -> tuple[list[Instruction], Instruction | None]:
        """
        Codegen based off of:
        with ctx(args):
            (rest)
        """
        # NOTE: we assume that TOS is a context manager CLASS!
        # pyrefly: ignore [implicit-any]
        load_args = []
        if self.target_values:
            load_args = [create_load_const(val) for val in self.target_values]

        create_ctx: list[Instruction] = []
        # Do not push NULL in Python 3.14+ since the NULL should be on the symbolic stack.
        if sys.version_info < (3, 14):
            _initial_push_null(create_ctx)
        create_ctx.extend(
            [
                *load_args,
                *create_call_function(len(load_args), False),
            ]
        )

        def _template(ctx: AbstractContextManager[Any], dummy: Any) -> None:
            with ctx:
                dummy

        setup_with, epilogue = _bytecode_from_template_with_split(
            _template, self.stack_index
        )
        cleanup[:] = epilogue + cleanup

        load_fast_ctx_inst = next(
            (
                inst
                for inst in setup_with
                if inst.opname in ("LOAD_FAST", "LOAD_FAST_BORROW")
                and inst.argval == "ctx"
            ),
            None,
        )
        assert load_fast_ctx_inst is not None
        # ctx already loaded on stack before the template - no need to LOAD_FAST
        overwrite_instruction(load_fast_ctx_inst, [create_instruction("NOP")])

        # 3.11+ only
        push_exc_info_gen = (
            inst for inst in epilogue if inst.opname == "PUSH_EXC_INFO"
        )
        push_exc_info_inst = next(push_exc_info_gen, None)
        # expect only 1 PUSH_EXC_INFO in epilogue
        assert next(push_exc_info_gen, None) is None

        return create_ctx + setup_with, push_exc_info_inst