def _get_analytic_account_ids_from_distributions(self, distributions):
        if not distributions:
            return []

        if isinstance(distributions, (list, tuple, set)):
            return {int(_id) for distribution in distributions for key in (distribution or {}) for _id in key.split(',')}
        else:
            return {int(_id) for key in (distributions or {}) for _id in key.split(',')}