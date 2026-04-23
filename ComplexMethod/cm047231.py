def _run(self, records, eval_context):
        self.ensure_one()
        if self.warning:
            raise ServerActionWithWarningsError(_("Server action %(action_name)s has one or more warnings, address them first.", action_name=self.name))

        runner, multi = self._get_runner()
        res = False
        if runner and multi:
            # call the multi method
            run_self = self.with_context(eval_context['env'].context)
            res = runner(run_self, eval_context=eval_context)
        elif runner:
            active_id = self.env.context.get('active_id')
            if not active_id and self.env.context.get('onchange_self'):
                active_id = self.env.context['onchange_self']._origin.id
                if not active_id:  # onchange on new record
                    res = runner(self, eval_context=eval_context)
            active_ids = self.env.context.get('active_ids', [active_id] if active_id else [])
            for active_id in active_ids:
                # run context dedicated to a particular active_id
                run_self = self.with_context(active_ids=[active_id], active_id=active_id)
                eval_context['env'] = eval_context['env'](context=run_self.env.context)
                eval_context['records'] = eval_context['record'] = records.browse(active_id)
                res = runner(run_self, eval_context=eval_context)
        else:
            _logger.warning(
                "Found no way to execute server action %r of type %r, ignoring it. "
                "Verify that the type is correct or add a method called "
                "`_run_action_<type>` or `_run_action_<type>_multi`.",
                self.name, self.state
            )
        return res or False