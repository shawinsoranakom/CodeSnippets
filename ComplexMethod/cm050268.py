def _sync_salary_distribution(self):
        for employee in self:
            current_salary_distribution = employee.salary_distribution or {}
            current_ids = set(map(int, current_salary_distribution.keys()))
            account_ids = set(employee.bank_account_ids.ids)

            added_ids = account_ids - current_ids
            removed_ids = current_ids - account_ids
            unchanged_ids = account_ids & current_ids

            # Preserve existing data and order
            ordered = sorted([
                (int(i), data) for i, data in current_salary_distribution.items()
                if int(i) in unchanged_ids
            ], key=lambda x: (not x[1].get('amount_is_percentage'), x[1].get('sequence', float('inf'))))

            new_salary_distribution = {str(i): data for i, data in ordered}

            # Redistribute removed % to first item
            removed_percentage = sum(current_salary_distribution[str(i)]['amount']
                for i in removed_ids if str(i) in current_salary_distribution and current_salary_distribution[str(i)]['amount_is_percentage'])
            if removed_percentage and ordered:
                first_id = str(ordered[0][0])
                if new_salary_distribution[first_id]['amount_is_percentage']:
                    new_salary_distribution[first_id]['amount'] += removed_percentage

            # Add new entries with remaining %
            total_allocated = sum(d['amount'] for d in new_salary_distribution.values() if d['amount_is_percentage'])
            remaining = max(0.0, 100.0 - total_allocated)
            seq = max((d.get('sequence', 0) for d in new_salary_distribution.values()), default=0)
            amount = employee.currency_id.round(remaining / len(added_ids)) if added_ids else 0.0
            for i, new_id in enumerate(added_ids):
                seq += 1
                if i == len(added_ids) - 1:
                    amount = remaining
                new_salary_distribution[str(new_id)] = {
                    'amount': amount,
                    'amount_is_percentage': True,
                    'sequence': seq,
                }
                remaining -= amount

            employee.salary_distribution = new_salary_distribution