def catcher_stmt(self):

        localctx = ASLParser.Catcher_stmtContext(self, self._ctx, self.state)
        self.enterRule(localctx, 194, self.RULE_catcher_stmt)
        try:
            self.state = 1062
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [122]:
                self.enterOuterAlt(localctx, 1)
                self.state = 1056
                self.error_equals_decl()
                pass
            elif token in [95]:
                self.enterOuterAlt(localctx, 2)
                self.state = 1057
                self.result_path_decl()
                pass
            elif token in [115]:
                self.enterOuterAlt(localctx, 3)
                self.state = 1058
                self.next_decl()
                pass
            elif token in [134]:
                self.enterOuterAlt(localctx, 4)
                self.state = 1059
                self.assign_decl()
                pass
            elif token in [135]:
                self.enterOuterAlt(localctx, 5)
                self.state = 1060
                self.output_decl()
                pass
            elif token in [10]:
                self.enterOuterAlt(localctx, 6)
                self.state = 1061
                self.comment_decl()
                pass
            else:
                raise NoViableAltException(self)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx