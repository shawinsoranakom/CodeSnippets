def _eval_value(self, eval_context=None):
        result = {}
        for action in self:
            expr = action.value
            if action.evaluation_type == 'equation':
                expr = safe_eval(action.value, eval_context)
            elif action.evaluation_type == 'sequence':
                expr = action.sequence_id.next_by_id()
            elif action.update_field_id.ttype in ['one2many', 'many2many']:
                operation = action.update_m2m_operation
                if operation == 'add':
                    expr = [Command.link(int(action.value))]
                elif operation == 'remove':
                    expr = [Command.unlink(int(action.value))]
                elif operation == 'set':
                    expr = [Command.set([int(action.value)])]
                elif operation == 'clear':
                    expr = [Command.clear()]
            elif action.update_field_id.ttype == 'boolean':
                expr = action.update_boolean_value == 'true'
            elif action.update_field_id.ttype in ['many2one', 'integer']:
                try:
                    expr = int(action.value)
                    if expr == 0 and action.update_field_id.ttype == 'many2one':
                        expr = False
                except Exception:
                    pass
            elif action.update_field_id.ttype == 'float':
                with contextlib.suppress(Exception):
                    expr = float(action.value)
            elif action.update_field_id.ttype == 'html':
                expr = action.html_value
            result[action.id] = expr
        return result