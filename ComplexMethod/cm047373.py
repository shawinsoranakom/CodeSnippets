def _compute_domain(self, model_name: str, mode: str = "read") -> Domain:
        model = self.env[model_name]

        # add rules for parent models
        global_domains: list[Domain] = []
        for parent_model_name, parent_field_name in model._inherits.items():
            if not model._fields[parent_field_name].store:
                continue
            if domain := self._compute_domain(parent_model_name, mode):
                global_domains.append(Domain(parent_field_name, 'any', domain))

        rules = self._get_rules(model_name, mode=mode)
        if not rules:
            return Domain.AND(global_domains).optimize(model)

        # browse user and rules with sudo to avoid access errors!
        eval_context = self._eval_context()
        user_groups = self.env.user.all_group_ids
        group_domains: list[Domain] = []
        for rule in rules.sudo():
            if rule.groups and not (rule.groups & user_groups):
                continue
            # evaluate the domain for the current user
            dom = Domain(safe_eval(rule.domain_force, eval_context)) if rule.domain_force else Domain.TRUE
            if rule.groups:
                group_domains.append(dom)
            else:
                global_domains.append(dom)

        # combine global domains and group domains
        if group_domains:
            global_domains.append(Domain.OR(group_domains))
        return Domain.AND(global_domains).optimize(model)