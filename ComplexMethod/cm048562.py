def copy(self, default=None):
        '''Copy the whole financial report hierarchy by duplicating each line recursively.

        :param default: Default values.
        :return: The copied account.report record.
        '''
        new_reports = super().copy(default=default)
        for old_report, new_report in zip(self, new_reports):
            code_mapping = {}
            for line in old_report.line_ids.filtered(lambda x: not x.parent_id):
                line._copy_hierarchy(new_report, code_mapping=code_mapping)

            # Replace line codes by their copy in aggregation formulas
            for expression in new_report.line_ids.expression_ids:
                if expression.engine == 'aggregation':
                    copied_formula = f" {expression.formula} "  # Add spaces so that the lookahead/lookbehind of the regex can work (we can't do a | in those)
                    for old_code, new_code in code_mapping.items():
                        copied_formula = re.sub(f"(?<=\\W){old_code}(?=\\W)", new_code, copied_formula)
                    expression.formula = copied_formula.strip()  # Remove the spaces introduced for lookahead/lookbehind
                    # Repeat the same logic for the subformula, if it is set.
                    if expression.subformula:
                        copied_subformula = f" {expression.subformula} "
                        for old_code, new_code in code_mapping.items():
                            copied_subformula = re.sub(f"(?<=\\W){old_code}(?=\\W)", new_code, copied_subformula)
                        expression.subformula = copied_subformula.strip()

            old_report.column_ids.copy({'report_id': new_report.id})
        return new_reports