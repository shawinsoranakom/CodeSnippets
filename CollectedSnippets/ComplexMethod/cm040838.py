def comparison_func(self):

        localctx = ASLParser.Comparison_funcContext(self, self._ctx, self.state)
        self.enterRule(localctx, 120, self.RULE_comparison_func)
        self._la = 0 # Token type
        try:
            self.state = 763
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,52,self._ctx)
            if la_ == 1:
                localctx = ASLParser.Condition_litContext(self, localctx)
                self.enterOuterAlt(localctx, 1)
                self.state = 749
                self.match(ASLParser.CONDITION)
                self.state = 750
                self.match(ASLParser.COLON)
                self.state = 751
                _la = self._input.LA(1)
                if not(_la==7 or _la==8):
                    self._errHandler.recoverInline(self)
                else:
                    self._errHandler.reportMatch(self)
                    self.consume()
                pass

            elif la_ == 2:
                localctx = ASLParser.Condition_string_jsonataContext(self, localctx)
                self.enterOuterAlt(localctx, 2)
                self.state = 752
                self.match(ASLParser.CONDITION)
                self.state = 753
                self.match(ASLParser.COLON)
                self.state = 754
                self.string_jsonata()
                pass

            elif la_ == 3:
                localctx = ASLParser.Comparison_func_string_variable_sampleContext(self, localctx)
                self.enterOuterAlt(localctx, 3)
                self.state = 755
                self.comparison_op()
                self.state = 756
                self.match(ASLParser.COLON)
                self.state = 757
                self.string_variable_sample()
                pass

            elif la_ == 4:
                localctx = ASLParser.Comparison_func_valueContext(self, localctx)
                self.enterOuterAlt(localctx, 4)
                self.state = 759
                self.comparison_op()
                self.state = 760
                self.match(ASLParser.COLON)
                self.state = 761
                self.json_value_decl()
                pass


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx