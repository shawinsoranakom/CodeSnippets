def emit_SimpleStmt(
        self,
        stmt: SimpleStmt,
        uop: CodeSection,
        storage: Storage,
        inst: Instruction | None,
    ) -> tuple[bool, Token | None, Storage]:
        local_stores = set(uop.local_stores)
        reachable = True
        tkn = stmt.contents[-1]
        try:
            if stmt in uop.properties.escaping_calls and not self.cannot_escape:
                escape = uop.properties.escaping_calls[stmt]
                if escape.kills is not None:
                    self.stackref_kill(escape.kills, storage, True)
                self.emit_save(storage)
            tkn_iter = TokenIterator(stmt.contents)
            for tkn in tkn_iter:
                if tkn.kind == "GOTO":
                    label_tkn = next(tkn_iter)
                    self.goto_label(tkn, label_tkn, storage)
                    reachable = False
                elif tkn.kind == "RETURN":
                    self.emit(tkn)
                    semicolon = emit_to(self.out, tkn_iter, "SEMI")
                    self.emit(semicolon)
                    reachable = False
                elif tkn.kind == "IDENTIFIER":
                    if tkn.text in self._replacers:
                        if not self._replacers[tkn.text](tkn, tkn_iter, uop, storage, inst):
                            reachable = False
                    else:
                        if tkn in local_stores:
                            for var in storage.inputs:
                                if var.name == tkn.text:
                                    var.in_local = True
                                    var.memory_offset = None
                                    break
                            for var in storage.outputs:
                                if var.name == tkn.text:
                                    var.in_local = True
                                    var.memory_offset = None
                                    break
                        if tkn.text.startswith("DISPATCH"):
                            reachable = False
                        self.out.emit(tkn)
                else:
                    self.out.emit(tkn)
            if stmt in uop.properties.escaping_calls and not self.cannot_escape:
                self.emit_reload(storage)
            return reachable, None, storage
        except StackError as ex:
            raise analysis_error(ex.args[0], tkn)