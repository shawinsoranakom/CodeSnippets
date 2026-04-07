def compile_nodelist(self):
        """
        Parse and compile the template source into a nodelist. If debug
        is True and an exception occurs during parsing, the exception is
        annotated with contextual line information where it occurred in the
        template source.
        """
        if self.engine.debug:
            lexer = DebugLexer(self.source)
        else:
            lexer = Lexer(self.source)

        tokens = lexer.tokenize()
        parser = Parser(
            tokens,
            self.engine.template_libraries,
            self.engine.template_builtins,
            self.origin,
        )

        try:
            nodelist = parser.parse()
            self.extra_data = parser.extra_data
            return nodelist
        except Exception as e:
            if self.engine.debug:
                e.template_debug = self.get_exception_info(e, e.token)
            if (
                isinstance(e, TemplateSyntaxError)
                and self.origin.name != UNKNOWN_SOURCE
                and e.args
            ):
                raw_message = e.args[0]
                e.raw_error_message = raw_message
                e.args = (f"Template: {self.origin.name}, {raw_message}", *e.args[1:])
            raise