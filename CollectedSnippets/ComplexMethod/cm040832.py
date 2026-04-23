def top_layer_stmt(self):

        localctx = ASLParser.Top_layer_stmtContext(self, self._ctx, self.state)
        self.enterRule(localctx, 4, self.RULE_top_layer_stmt)
        try:
            self.state = 252
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [10]:
                self.enterOuterAlt(localctx, 1)
                self.state = 246
                self.comment_decl()
                pass
            elif token in [14]:
                self.enterOuterAlt(localctx, 2)
                self.state = 247
                self.version_decl()
                pass
            elif token in [131]:
                self.enterOuterAlt(localctx, 3)
                self.state = 248
                self.query_language_decl()
                pass
            elif token in [12]:
                self.enterOuterAlt(localctx, 4)
                self.state = 249
                self.startat_decl()
                pass
            elif token in [11]:
                self.enterOuterAlt(localctx, 5)
                self.state = 250
                self.states_decl()
                pass
            elif token in [75, 76]:
                self.enterOuterAlt(localctx, 6)
                self.state = 251
                self.timeout_seconds_decl()
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