def _create_report_expression(self, engine):
        # create account.report.expression for each report line based on the formula provided to each
        # engine-related field. This makes xmls a bit shorter
        vals_list = []
        xml_ids = self.expression_ids.filtered(lambda exp: exp.label == 'balance').get_external_id()
        for report_line in self:
            if engine == 'domain' and report_line.domain_formula:
                subformula, formula = DOMAIN_REGEX.match(report_line.domain_formula or '').groups()
                # Resolve the calls to ref(), to mimic the fact those formulas are normally given with an eval="..." in XML
                formula = re.sub(r'''\bref\((?P<quote>['"])(?P<xmlid>.+?)(?P=quote)\)''', lambda m: str(self.env.ref(m['xmlid']).id), formula)
            elif engine == 'account_codes' and report_line.account_codes_formula:
                subformula, formula = None, report_line.account_codes_formula
            elif engine == 'aggregation' and report_line.aggregation_formula:
                subformula, formula = None, report_line.aggregation_formula
            elif engine == 'external' and report_line.external_formula:
                subformula, formula = 'editable', 'most_recent'
                if report_line.external_formula == 'percentage':
                    subformula = 'editable;rounding=0'
                elif report_line.external_formula == 'monetary':
                    formula = 'sum'
            elif engine == 'tax_tags' and report_line.tax_tags_formula:
                subformula, formula = None, report_line.tax_tags_formula
            else:
                # If we want to replace a formula shortcut with a full-syntax expression, we need to make the formula field falsy
                # We can't simply remove it from the xml because it won't be updated
                # If the formula field is falsy, we need to remove the expression that it generated
                report_line.expression_ids.filtered(lambda exp: exp.engine == engine and exp.label == 'balance' and not xml_ids.get(exp.id)).unlink()
                continue

            vals = {
                'report_line_id': report_line.id,
                'label': 'balance',
                'engine': engine,
                'formula': formula.lstrip(' \t\n'),  # Avoid IndentationError in evals
                'subformula': subformula
            }
            if engine == 'external' and report_line.external_formula:
                vals['figure_type'] = report_line.external_formula

            if report_line.expression_ids:
                # expressions already exists, update the first expression with the right engine
                # since syntactic sugar aren't meant to be used with multiple expressions
                for expression in report_line.expression_ids:
                    if expression.label == 'balance':
                        # If we had a 'balance' expression coming from the xml and are using a formula shortcut on top of it,
                        # we expect the shortcut to replace the original expression. The full declaration should also
                        # be removed from the data file, leading to the ORM deleting it automatically.
                        if xml_ids.get(expression.id):
                            expression.unlink()
                            vals_list.append(vals)
                        else:
                            expression.write(vals)
                        break
            else:
                # else prepare batch creation
                vals_list.append(vals)

        if vals_list:
            self.env['account.report.expression'].create(vals_list)