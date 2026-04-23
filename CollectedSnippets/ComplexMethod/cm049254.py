def _get_action(self, subpath):
        def get_action_triples_():
            try:
                yield from get_action_triples(request.env, subpath, start_pos=1)
            except ValueError as exc:
                raise BadRequest(exc.args[0]) from exc

        context = dict(request.env.context)
        active_id, action, record_id = list(get_action_triples_())[-1]
        action = action.sudo()
        if action.usage == 'ir_actions_server' and action.path:
            # force read-only evaluation of action_data
            try:
                with action.pool.cursor(readonly=True) as ro_cr:
                    if not ro_cr.readonly:
                        ro_cr.connection.set_session(readonly=True)
                    assert ro_cr.readonly
                    action_data = action.with_env(action.env(cr=ro_cr, su=False)).run()
            except psycopg2.errors.ReadOnlySqlTransaction as e:
                # never retry on RO connection, just leave
                raise AccessError(action.env._("Unsupported server action")) from e
            except ValueError as e:
                # safe_eval wraps the error into a ValueError (as str)
                if "ReadOnlySqlTransaction" not in e.args[0]:
                    raise
                raise AccessError(action.env._("Unsupported server action")) from e
            # transform data into a new record
            action = action.env[action_data['type']]
            action = action.new(action_data, origin=action.browse(action_data.pop('id')))
        if action._name != 'ir.actions.act_window':
            e = f"{action._name} are not supported server-side"
            raise BadRequest(e)
        eval_context = dict(
            action._get_eval_context(action),
            active_id=active_id,
            context=context,
            allowed_company_ids=request.env.user.company_ids.ids,
        )
        # update the context and return
        context.update(safe_eval(action.context, eval_context))
        return action, context, eval_context, record_id