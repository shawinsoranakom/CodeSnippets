def _patch_view(self, arch, view, view_type):
        if not self.env.context.get("studio") and self.env['account.analytic.plan'].has_access('read'):
            project_plan, other_plans = self.env['account.analytic.plan']._get_all_plans()

            # Find main account nodes
            account_node = arch.find('.//field[@name="account_id"]')
            account_filter_node = arch.find('.//filter[@name="account_id"]')

            # Force domain on main account node as the fields_get doesn't do the trick
            if account_node is not None and view_type == 'search':
                account_node.set('domain', repr(self._get_plan_domain(project_plan)))

            # If there is a main node, append the ones for other plans
            if account_node is not None:
                account_node.set('context', repr(self._get_account_node_context(project_plan)))
                for plan in other_plans[::-1]:
                    fname = plan._column_name()
                    if account_node is not None:
                        account_node.addnext(E.field(**{
                            'optional': 'show',
                            **account_node.attrib,
                            'name': fname,
                            'domain': repr(self._get_plan_domain(plan)),
                            'context': repr(self._get_account_node_context(plan)),
                        }))
            if account_filter_node is not None:
                for plan in other_plans[::-1] + project_plan:
                    fname = plan._column_name()
                    if plan != project_plan:
                        account_filter_node.addnext(E.filter(name=fname, context=f"{{'group_by': '{fname}'}}"))
                    current = plan
                    while current := current.children_ids:
                        _depth, subfname = current[0]._hierarchy_name()
                        if subfname in self._fields:
                            account_filter_node.addnext(E.filter(name=subfname, context=f"{{'group_by': '{subfname}'}}"))
        return arch, view