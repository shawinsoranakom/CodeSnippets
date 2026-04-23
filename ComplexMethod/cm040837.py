def comparison_variable_stmt(self):

        localctx = ASLParser.Comparison_variable_stmtContext(self, self._ctx, self.state)
        self.enterRule(localctx, 112, self.RULE_comparison_variable_stmt)
        try:
            self.state = 721
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [26]:
                self.enterOuterAlt(localctx, 1)
                self.state = 715
                self.variable_decl()
                pass
            elif token in [25, 30, 31, 32, 33, 34, 35, 36, 37, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70]:
                self.enterOuterAlt(localctx, 2)
                self.state = 716
                self.comparison_func()
                pass
            elif token in [115]:
                self.enterOuterAlt(localctx, 3)
                self.state = 717
                self.next_decl()
                pass
            elif token in [134]:
                self.enterOuterAlt(localctx, 4)
                self.state = 718
                self.assign_decl()
                pass
            elif token in [135]:
                self.enterOuterAlt(localctx, 5)
                self.state = 719
                self.output_decl()
                pass
            elif token in [10]:
                self.enterOuterAlt(localctx, 6)
                self.state = 720
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