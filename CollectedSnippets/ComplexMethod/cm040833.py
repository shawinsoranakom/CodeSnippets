def state_stmt(self):

        localctx = ASLParser.State_stmtContext(self, self._ctx, self.state)
        self.enterRule(localctx, 14, self.RULE_state_stmt)
        try:
            self.state = 308
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [10]:
                self.enterOuterAlt(localctx, 1)
                self.state = 270
                self.comment_decl()
                pass
            elif token in [131]:
                self.enterOuterAlt(localctx, 2)
                self.state = 271
                self.query_language_decl()
                pass
            elif token in [15]:
                self.enterOuterAlt(localctx, 3)
                self.state = 272
                self.type_decl()
                pass
            elif token in [91]:
                self.enterOuterAlt(localctx, 4)
                self.state = 273
                self.input_path_decl()
                pass
            elif token in [90]:
                self.enterOuterAlt(localctx, 5)
                self.state = 274
                self.resource_decl()
                pass
            elif token in [115]:
                self.enterOuterAlt(localctx, 6)
                self.state = 275
                self.next_decl()
                pass
            elif token in [96]:
                self.enterOuterAlt(localctx, 7)
                self.state = 276
                self.result_decl()
                pass
            elif token in [95]:
                self.enterOuterAlt(localctx, 8)
                self.state = 277
                self.result_path_decl()
                pass
            elif token in [92]:
                self.enterOuterAlt(localctx, 9)
                self.state = 278
                self.output_path_decl()
                pass
            elif token in [116]:
                self.enterOuterAlt(localctx, 10)
                self.state = 279
                self.end_decl()
                pass
            elif token in [27]:
                self.enterOuterAlt(localctx, 11)
                self.state = 280
                self.default_decl()
                pass
            elif token in [24]:
                self.enterOuterAlt(localctx, 12)
                self.state = 281
                self.choices_decl()
                pass
            elif token in [119, 120]:
                self.enterOuterAlt(localctx, 13)
                self.state = 282
                self.error_decl()
                pass
            elif token in [117, 118]:
                self.enterOuterAlt(localctx, 14)
                self.state = 283
                self.cause_decl()
                pass
            elif token in [71, 72]:
                self.enterOuterAlt(localctx, 15)
                self.state = 284
                self.seconds_decl()
                pass
            elif token in [73, 74]:
                self.enterOuterAlt(localctx, 16)
                self.state = 285
                self.timestamp_decl()
                pass
            elif token in [93]:
                self.enterOuterAlt(localctx, 17)
                self.state = 286
                self.items_decl()
                pass
            elif token in [94]:
                self.enterOuterAlt(localctx, 18)
                self.state = 287
                self.items_path_decl()
                pass
            elif token in [85]:
                self.enterOuterAlt(localctx, 19)
                self.state = 288
                self.item_processor_decl()
                pass
            elif token in [86]:
                self.enterOuterAlt(localctx, 20)
                self.state = 289
                self.iterator_decl()
                pass
            elif token in [87]:
                self.enterOuterAlt(localctx, 21)
                self.state = 290
                self.item_selector_decl()
                pass
            elif token in [102]:
                self.enterOuterAlt(localctx, 22)
                self.state = 291
                self.item_reader_decl()
                pass
            elif token in [88, 89]:
                self.enterOuterAlt(localctx, 23)
                self.state = 292
                self.max_concurrency_decl()
                pass
            elif token in [75, 76]:
                self.enterOuterAlt(localctx, 24)
                self.state = 293
                self.timeout_seconds_decl()
                pass
            elif token in [77, 78]:
                self.enterOuterAlt(localctx, 25)
                self.state = 294
                self.heartbeat_seconds_decl()
                pass
            elif token in [28]:
                self.enterOuterAlt(localctx, 26)
                self.state = 295
                self.branches_decl()
                pass
            elif token in [97]:
                self.enterOuterAlt(localctx, 27)
                self.state = 296
                self.parameters_decl()
                pass
            elif token in [121]:
                self.enterOuterAlt(localctx, 28)
                self.state = 297
                self.retry_decl()
                pass
            elif token in [130]:
                self.enterOuterAlt(localctx, 29)
                self.state = 298
                self.catch_decl()
                pass
            elif token in [101]:
                self.enterOuterAlt(localctx, 30)
                self.state = 299
                self.result_selector_decl()
                pass
            elif token in [109, 110]:
                self.enterOuterAlt(localctx, 31)
                self.state = 300
                self.tolerated_failure_count_decl()
                pass
            elif token in [111, 112]:
                self.enterOuterAlt(localctx, 32)
                self.state = 301
                self.tolerated_failure_percentage_decl()
                pass
            elif token in [113]:
                self.enterOuterAlt(localctx, 33)
                self.state = 302
                self.label_decl()
                pass
            elif token in [114]:
                self.enterOuterAlt(localctx, 34)
                self.state = 303
                self.result_writer_decl()
                pass
            elif token in [134]:
                self.enterOuterAlt(localctx, 35)
                self.state = 304
                self.assign_decl()
                pass
            elif token in [136]:
                self.enterOuterAlt(localctx, 36)
                self.state = 305
                self.arguments_decl()
                pass
            elif token in [135]:
                self.enterOuterAlt(localctx, 37)
                self.state = 306
                self.output_decl()
                pass
            elif token in [98]:
                self.enterOuterAlt(localctx, 38)
                self.state = 307
                self.credentials_decl()
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