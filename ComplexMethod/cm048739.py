def _constrains_matching_number(self):
        for line in self:
            if line.matching_number:
                if not re.match(r'^((P?\d+)|(I.+))$', line.matching_number):
                    raise Exception("Invalid matching number format")
                elif line.matching_number.startswith('I') and (line.matched_debit_ids or line.matched_credit_ids):
                    raise ValidationError(_("A temporary number can not be used in a real matching"))
                elif line.matching_number.startswith('P') and not (line.matched_debit_ids or line.matched_credit_ids):
                    raise Exception("Should have partials")
                elif line.matching_number.startswith('P') and line.full_reconcile_id:
                    raise Exception("Should not be partial number")
                elif line.matching_number.isdecimal() and not line.full_reconcile_id:
                    raise Exception("Should not be full number")
                elif line.full_reconcile_id and line.matching_number != str(line.full_reconcile_id.id):
                    raise Exception("Matching number should be the full reconcile")
            elif line.matched_debit_ids or line.matched_credit_ids:
                raise Exception("Should have number")