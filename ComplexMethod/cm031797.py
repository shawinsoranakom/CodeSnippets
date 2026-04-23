def emit_MacroIfStmt(
        self,
        stmt: MacroIfStmt,
        uop: CodeSection,
        storage: Storage,
        inst: Instruction | None,
    ) -> tuple[bool, Token | None, Storage]:
        self.out.emit(stmt.condition)
        branch = stmt.else_ is not None
        reachable = True
        if_storage = storage
        else_storage = storage.copy()
        for s in stmt.body:
            r, tkn, if_storage = self._emit_stmt(s, uop, if_storage, inst)
            if tkn is not None:
                self.out.emit(tkn)
            if not r:
                reachable = False
        if branch:
            assert stmt.else_ is not None
            self.out.emit(stmt.else_)
            assert stmt.else_body is not None
            for s in stmt.else_body:
                r, tkn, else_storage = self._emit_stmt(s, uop, else_storage, inst)
                if tkn is not None:
                    self.out.emit(tkn)
                if not r:
                    reachable = False
            else_storage.merge(if_storage, self.out)
            storage = if_storage
        else:
            if_storage.merge(else_storage, self.out)
            storage = else_storage
        self.out.emit(stmt.endif)
        return reachable, None, storage