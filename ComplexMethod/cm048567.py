def _get_aggregation_terms_details(self):
        """ Computes the details of each aggregation expression in self, and returns them in the form of a single dict aggregating all the results.

        Example of aggregation details:
        formula 'A.balance + B.balance + A.other'
        will return: {'A': {'balance', 'other'}, 'B': {'balance'}}
        """
        totals_by_code = defaultdict(set)
        for expression in self:
            if expression.engine != 'aggregation':
                raise UserError(_("Cannot get aggregation details from a line not using 'aggregation' engine"))

            expression_terms = re.split('[-+/*]', re.sub(r'[\s()]', '', expression.formula))
            for term in expression_terms:
                if term and not re.match(r'^([0-9]*[.])?[0-9]*$', term): # term might be empty if the formula contains a negative term
                    line_code, total_name = term.split('.')
                    totals_by_code[line_code].add(total_name)

            if expression.subformula:
                if_other_expr_match = re.match(r'if_other_expr_(above|below)\((?P<line_code>.+)[.](?P<expr_label>.+),.+\)', expression.subformula)
                if if_other_expr_match:
                    totals_by_code[if_other_expr_match['line_code']].add(if_other_expr_match['expr_label'])

        return totals_by_code