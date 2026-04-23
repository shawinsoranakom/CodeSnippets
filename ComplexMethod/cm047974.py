def _filter_pre(self, records, feedback=False):
        """ Filter the records that satisfy the precondition of automation ``self``. """
        self_sudo = self.sudo()
        if self_sudo.filter_pre_domain and records:
            if feedback:
                # this context flag enables to detect the executions of
                # automations while evaluating their precondition
                records = records.with_context(__action_feedback=True)
            domain = safe_eval.safe_eval(self_sudo.filter_pre_domain, self._get_eval_context())
            # keep computed fields depending on the currently changed field
            # as-is so they are recomputed after the value is set
            # see `test_computation_sequence`
            changed_fields = self.env.context.get('changed_fields', ())
            to_compute = {
                dep: comp
                for f in changed_fields
                for dep in self.env.registry.get_dependent_fields(f)
                if (comp := self.env.records_to_compute(dep))
            }
            records = records.with_context(changed_fields=()).sudo().filtered_domain(domain).sudo(records.env.su)
            for dep, comp in to_compute.items():
                self.env.add_to_compute(dep, comp)
        return records