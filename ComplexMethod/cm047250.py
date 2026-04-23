def _generate_speedscope(self, params):
        init_stack_trace = self[0].init_stack_trace
        for record in self:
            if record.init_stack_trace != init_stack_trace:
                raise UserError(self.env._('All profiles must have the same initial stack trace to be displayed together.'))
        sp = Speedscope(init_stack_trace=json.loads(init_stack_trace))
        for profile in self:
            if (params['sql_no_gap_profile'] or params['sql_density_profile'] or params['combined_profile']) and profile.sql:
                sp.add(f'sql {profile.id}', json.loads(profile.sql))
            if (params['frames_profile'] or params['combined_profile']) and profile.traces_async:
                sp.add(f'frames {profile.id}', json.loads(profile.traces_async))
            if params['profile_aggregation_mode'] == 'tabs':
                profile._add_outputs(sp, f'{profile.id} {profile.name}' if len(self) > 1 else '', params)

        if params['profile_aggregation_mode'] == 'temporal':
            self._add_outputs(sp, 'all', params)

        result = json.dumps(sp.make(**params))
        return result.encode('utf-8')