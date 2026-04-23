def base_automation_onchange(self):
                automation_rule = self.env['base.automation'].browse(automation_rule_id)

                if not automation_rule._filter_post(self):
                    # Do nothing if onchange record does not satisfy the filter_domain
                    return

                result = {}
                actions = automation_rule.sudo().action_server_ids.with_context(
                    active_model=self._name,
                    active_id=self._origin.id,
                    active_ids=self._origin.ids,
                    onchange_self=self,
                )
                for action in actions:
                    try:
                        res = action.run()
                    except Exception as e:
                        automation_rule._add_postmortem(e)
                        raise

                    if res:
                        if 'value' in res:
                            res['value'].pop('id', None)
                            self.update({key: val for key, val in res['value'].items() if key in self._fields})
                        if 'domain' in res:
                            result.setdefault('domain', {}).update(res['domain'])
                        if 'warning' in res:
                            result['warning'] = res["warning"]
                return result