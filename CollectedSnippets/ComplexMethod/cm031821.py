def stmt(self) -> Stmt:
        if tkn := self.expect(lx.IF):
            return self.if_stmt(tkn)
        elif self.expect(lx.LBRACE):
            self.backup()
            return self.block()
        elif tkn := self.expect(lx.FOR):
            return self.for_stmt(tkn)
        elif tkn := self.expect(lx.WHILE):
            return self.while_stmt(tkn)
        elif tkn := self.expect(lx.CMACRO_IF):
            return self.macro_if(tkn)
        elif tkn := self.expect(lx.CMACRO_ELSE):
            msg = "Unexpected #else"
            raise self.make_syntax_error(msg)
        elif tkn := self.expect(lx.CMACRO_ENDIF):
            msg = "Unexpected #endif"
            raise self.make_syntax_error(msg)
        elif tkn := self.expect(lx.CMACRO_OTHER):
            return SimpleStmt([tkn])
        elif tkn := self.expect(lx.SWITCH):
            msg = "switch statements are not supported due to their complex flow control. Sorry."
            raise self.make_syntax_error(msg)
        tokens = self.consume_to(lx.SEMI)
        return SimpleStmt(tokens)