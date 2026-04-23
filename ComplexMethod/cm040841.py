def json_value_decl(self):

        localctx = ASLParser.Json_value_declContext(self, self._ctx, self.state)
        self.enterRule(localctx, 210, self.RULE_json_value_decl)
        try:
            self.state = 1117
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,84,self._ctx)
            if la_ == 1:
                self.enterOuterAlt(localctx, 1)
                self.state = 1108
                self.match(ASLParser.NUMBER)
                pass

            elif la_ == 2:
                self.enterOuterAlt(localctx, 2)
                self.state = 1109
                self.match(ASLParser.INT)
                pass

            elif la_ == 3:
                self.enterOuterAlt(localctx, 3)
                self.state = 1110
                self.match(ASLParser.TRUE)
                pass

            elif la_ == 4:
                self.enterOuterAlt(localctx, 4)
                self.state = 1111
                self.match(ASLParser.FALSE)
                pass

            elif la_ == 5:
                self.enterOuterAlt(localctx, 5)
                self.state = 1112
                self.match(ASLParser.NULL)
                pass

            elif la_ == 6:
                self.enterOuterAlt(localctx, 6)
                self.state = 1113
                self.json_binding()
                pass

            elif la_ == 7:
                self.enterOuterAlt(localctx, 7)
                self.state = 1114
                self.json_arr_decl()
                pass

            elif la_ == 8:
                self.enterOuterAlt(localctx, 8)
                self.state = 1115
                self.json_obj_decl()
                pass

            elif la_ == 9:
                self.enterOuterAlt(localctx, 9)
                self.state = 1116
                self.string_literal()
                pass


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx