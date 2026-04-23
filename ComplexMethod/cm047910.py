def _merge_distribution(self, old_distribution: dict, new_distribution: dict) -> dict:
        if '__update__' not in new_distribution:
            return new_distribution  # update everything by default

        non_changing_values, changing_values, non_changing_amount, changing_amount = self._modifiying_distribution_values(
            old_distribution,
            new_distribution,
        )
        if non_changing_amount > changing_amount:
            ratio = changing_amount / non_changing_amount
            additional_vals = {
                ','.join(map(str, old_key)): old_val * (1 - ratio)
                for old_key, old_val in non_changing_values.items()
                if old_key
            }
            ratio = 1
        elif changing_amount > non_changing_amount:
            ratio = non_changing_amount / changing_amount
            additional_vals = {
                ','.join(map(str, new_key)): new_val * (1 - ratio)
                for new_key, new_val in changing_values.items()
                if new_key
            }
        else:
            ratio = 1
            additional_vals = {}

        return {
            ','.join(map(str, old_key + new_key)): ratio * old_val * new_val / non_changing_amount
            for old_key, old_val in non_changing_values.items()
            for new_key, new_val in changing_values.items()
        } | additional_vals