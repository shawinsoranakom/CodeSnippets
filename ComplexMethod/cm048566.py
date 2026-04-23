def _expand_aggregations(self):
        """Return self and its full aggregation expression dependency"""
        result = self

        to_expand = self.filtered(lambda x: x.engine == 'aggregation')
        while to_expand:
            domains = []
            sub_expressions = self.env['account.report.expression']

            for candidate_expr in to_expand:
                if candidate_expr.formula == 'sum_children':
                    sub_expressions |= candidate_expr.report_line_id.children_ids.expression_ids.filtered(lambda e: e.label == candidate_expr.label)
                else:
                    labels_by_code = candidate_expr._get_aggregation_terms_details()

                    if candidate_expr.subformula and candidate_expr.subformula.startswith('cross_report'):
                        subformula_match = CROSS_REPORT_REGEX.match(candidate_expr.subformula)
                        if not subformula_match:
                            raise UserError(_(
                                "In report '%(report_name)s', on line '%(line_name)s', with label '%(label)s',\n"
                                "The format of the cross report expression is invalid. \n"
                                "Expected: cross_report(<report_id>|<xml_id>)"
                                "Example:  cross_report(my_module.my_report) or cross_report(123)",
                                report_name=candidate_expr.report_line_id.report_id.display_name,
                                line_name=candidate_expr.report_line_name,
                                label=candidate_expr.label,
                            ))
                        cross_report_value = subformula_match.groups()[0]
                        try:
                            report_id = int(cross_report_value)
                        except ValueError:
                            report_id = report.id if (report := self.env.ref(cross_report_value, raise_if_not_found=False)) else None

                        if not report_id:
                            raise UserError(_(
                                "In report '%(report_name)s', on line '%(line_name)s', with label '%(label)s',\n"
                                "Failed to parse the cross report id or xml_id.\n",
                                report_name=candidate_expr.report_line_id.report_id.display_name,
                                line_name=candidate_expr.report_line_name,
                                label=candidate_expr.label,
                            ))
                        elif report_id == candidate_expr.report_line_id.report_id.id:
                            raise UserError(_("You cannot use cross report on itself"))

                        cross_report_domain = [('report_line_id.report_id', '=', report_id)]
                    else:
                        cross_report_domain = [('report_line_id.report_id', '=', candidate_expr.report_line_id.report_id.id)]

                    for line_code, expr_labels in labels_by_code.items():
                        dependency_domain = [('report_line_id.code', '=', line_code), ('label', 'in', tuple(expr_labels))] + cross_report_domain
                        domains.append(dependency_domain)

            if domains:
                sub_expressions |= self.env['account.report.expression'].search(Domain.OR(domains))

            to_expand = sub_expressions.filtered(lambda x: x.engine == 'aggregation' and x not in result)
            result |= sub_expressions

        return result