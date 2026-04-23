def func_arg(self):

        localctx = ASLIntrinsicParser.Func_argContext(self, self._ctx, self.state)
        self.enterRule(localctx, 8, self.RULE_func_arg)
        self._la = 0 # Token type
        try:
            self.state = 43
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [30]:
                localctx = ASLIntrinsicParser.Func_arg_stringContext(self, localctx)
                self.enterOuterAlt(localctx, 1)
                self.state = 35
                self.match(ASLIntrinsicParser.STRING)
                pass
            elif token in [31]:
                localctx = ASLIntrinsicParser.Func_arg_intContext(self, localctx)
                self.enterOuterAlt(localctx, 2)
                self.state = 36
                self.match(ASLIntrinsicParser.INT)
                pass
            elif token in [32]:
                localctx = ASLIntrinsicParser.Func_arg_floatContext(self, localctx)
                self.enterOuterAlt(localctx, 3)
                self.state = 37
                self.match(ASLIntrinsicParser.NUMBER)
                pass
            elif token in [9, 10]:
                localctx = ASLIntrinsicParser.Func_arg_boolContext(self, localctx)
                self.enterOuterAlt(localctx, 4)
                self.state = 38
                _la = self._input.LA(1)
                if not(_la==9 or _la==10):
                    self._errHandler.recoverInline(self)
                else:
                    self._errHandler.reportMatch(self)
                    self.consume()
                pass
            elif token in [1]:
                localctx = ASLIntrinsicParser.Func_arg_context_pathContext(self, localctx)
                self.enterOuterAlt(localctx, 5)
                self.state = 39
                self.match(ASLIntrinsicParser.CONTEXT_PATH_STRING)
                pass
            elif token in [2]:
                localctx = ASLIntrinsicParser.Func_arg_json_pathContext(self, localctx)
                self.enterOuterAlt(localctx, 6)
                self.state = 40
                self.match(ASLIntrinsicParser.JSON_PATH_STRING)
                pass
            elif token in [3]:
                localctx = ASLIntrinsicParser.Func_arg_varContext(self, localctx)
                self.enterOuterAlt(localctx, 7)
                self.state = 41
                self.match(ASLIntrinsicParser.STRING_VARIABLE)
                pass
            elif token in [11]:
                localctx = ASLIntrinsicParser.Func_arg_func_declContext(self, localctx)
                self.enterOuterAlt(localctx, 8)
                self.state = 42
                self.states_func_decl()
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