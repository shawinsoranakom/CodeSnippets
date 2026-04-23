def emit_IfStmt(
        self,
        stmt: IfStmt,
        uop: CodeSection,
        storage: Storage,
        inst: Instruction | None,
    ) -> tuple[bool, Token | None, Storage]:
        self.out.emit(stmt.if_)
        for tkn in stmt.condition:
            self.out.emit(tkn)
        if_storage = storage.copy()
        rbrace: Token | None = stmt.if_
        try:
            reachable, rbrace, if_storage = self._emit_stmt(stmt.body, uop, if_storage, inst)
            if stmt.else_ is not None:
                assert rbrace is not None
                self.out.emit(rbrace)
                self.out.emit(stmt.else_)
            if stmt.else_body is not None:
                else_reachable, rbrace, else_storage = self._emit_stmt(stmt.else_body, uop, storage, inst)
                if not reachable:
                    reachable, storage = else_reachable, else_storage
                elif not else_reachable:
                    # Discard the else storage
                    storage = if_storage
                else:
                    #Both reachable
                    else_storage.merge(if_storage, self.out)
                    storage = else_storage
            else:
                if reachable:
                    if_storage.merge(storage, self.out)
                    storage = if_storage
                else:
                    # Discard the if storage
                    reachable = True
            return reachable, rbrace, storage
        except StackError as ex:
            assert rbrace is not None
            raise analysis_error(ex.args[0], rbrace) from None