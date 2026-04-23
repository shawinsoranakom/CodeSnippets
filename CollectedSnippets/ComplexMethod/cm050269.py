def _check_salary_distribution(self):
        for employee in self:
            dist = employee.salary_distribution
            if not dist:
                continue

            total = 0
            check_total = False
            for ba_values in dist.values():
                amount = ba_values.get('amount')
                is_percentage = ba_values.get('amount_is_percentage', True)
                if is_percentage and (not isinstance(amount, (float, int)) or not (0 <= amount <= 100)):
                    raise ValidationError(self.env._("Each amount percentage must be a number between 0 and 100."))
                if is_percentage:
                    check_total = True
                    total += amount

            if check_total and not float_is_zero(total - 100.0, precision_digits=4):
                raise ValidationError(self.env._("Total salary distribution on bank accounts must be exactly 100%."))