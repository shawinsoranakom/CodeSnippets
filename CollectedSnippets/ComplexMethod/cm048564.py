def _check_formula(self):
        def raise_formula_error(expression):
            raise ValidationError(self.env._("Invalid formula for expression '%(label)s' of line '%(line)s': %(formula)s",
                                    label=expression.label, line=expression.report_line_name,
                                    formula=expression.formula))

        expressions_by_engine = self.grouped('engine')
        for expression in expressions_by_engine.get('domain', []):
            try:
                domain = ast.literal_eval(expression.formula)
                self.env['account.move.line']._search(domain)
            except:
                raise_formula_error(expression)

        for expression in expressions_by_engine.get('account_codes', []):
            for token in ACCOUNT_CODES_ENGINE_SPLIT_REGEX.split(expression.formula.replace(' ', '')):
                if token:  # e.g. if the first character of the formula is "-", the first token is ''
                    token_match = ACCOUNT_CODES_ENGINE_TERM_REGEX.match(token)
                    prefix = token_match and token_match['prefix']
                    if not prefix:
                        raise_formula_error(expression)

        for expression in expressions_by_engine.get('aggregation', []):
            if not AGGREGATION_ENGINE_FORMULA_REGEX.fullmatch(expression.formula):
                raise_formula_error(expression)