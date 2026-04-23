def update_goal(self):
        """Update the goals to recomputes values and change of states

        If a manual goal is not updated for enough time, the user will be
        reminded to do so (done only once, in 'inprogress' state).
        If a goal reaches the target value, the status is set to reached
        If the end date is passed (at least +1 day, time not considered) without
        the target value being reached, the goal is set as failed."""
        goals_by_definition = {}
        for goal in self.with_context(prefetch_fields=False):
            goals_by_definition.setdefault(goal.definition_id, []).append(goal)

        for definition, goals in goals_by_definition.items():
            goals_to_write = {}
            if definition.computation_mode == 'manually':
                for goal in goals:
                    goals_to_write[goal] = goal._check_remind_delay()
            elif definition.computation_mode == 'python':
                # TODO batch execution
                for goal in goals:
                    # execute the chosen method
                    cxt = {
                        'object': goal,
                        'env': self.env,

                        'date': date,
                        'datetime': datetime,
                        'timedelta': timedelta,
                        'time': time,
                    }
                    code = definition.compute_code.strip()
                    safe_eval(code, cxt, mode="exec")
                    # the result of the evaluated codeis put in the 'result' local variable, propagated to the context
                    result = cxt.get('result')
                    if isinstance(result, (float, int)):
                        goals_to_write.update(goal._get_write_values(result))
                    else:
                        _logger.error(
                            "Invalid return content '%r' from the evaluation "
                            "of code for definition %s, expected a number",
                            result, definition.name)

            elif definition.computation_mode in ('count', 'sum'):  # count or sum
                Obj = self.env[definition.model_id.model]

                field_date_name = definition.field_date_id.name
                if definition.batch_mode:
                    # batch mode, trying to do as much as possible in one request
                    general_domain = ast.literal_eval(definition.domain)
                    field_name = definition.batch_distinctive_field.name
                    subqueries = {}
                    for goal in goals:
                        start_date = field_date_name and goal.start_date or False
                        end_date = field_date_name and goal.end_date or False
                        subqueries.setdefault((start_date, end_date), {}).update({goal.id:safe_eval(definition.batch_user_expression, {'user': goal.user_id})})

                    # the global query should be split by time periods (especially for recurrent goals)
                    for (start_date, end_date), query_goals in subqueries.items():
                        subquery_domain = list(general_domain)
                        subquery_domain.append((field_name, 'in', list(set(query_goals.values()))))
                        if start_date:
                            subquery_domain.append((field_date_name, '>=', start_date))
                        if end_date:
                            subquery_domain.append((field_date_name, '<=', end_date))

                        if definition.computation_mode == 'count':
                            user_values = Obj._read_group(subquery_domain, groupby=[field_name], aggregates=['__count'])

                        else:  # sum
                            value_field_name = definition.field_id.name
                            user_values = Obj._read_group(subquery_domain, groupby=[field_name], aggregates=[f'{value_field_name}:sum'])

                        # user_values has format of _read_group: [(<partner>, <aggregate>), ...]
                        for goal in [g for g in goals if g.id in query_goals]:
                            for field_value, aggregate in user_values:
                                queried_value = field_value.id if isinstance(field_value, models.Model) else field_value
                                if queried_value == query_goals[goal.id]:
                                    goals_to_write.update(goal._get_write_values(aggregate))

                else:
                    field_name = definition.field_id.name
                    field = Obj._fields.get(field_name)
                    sum_supported = bool(field) and field.type in {'integer', 'float', 'monetary'}
                    for goal in goals:
                        # eval the domain with user replaced by goal user object
                        domain = safe_eval(definition.domain, {'user': goal.user_id})

                        # add temporal clause(s) to the domain if fields are filled on the goal
                        if goal.start_date and field_date_name:
                            domain.append((field_date_name, '>=', goal.start_date))
                        if goal.end_date and field_date_name:
                            domain.append((field_date_name, '<=', goal.end_date))

                        if definition.computation_mode == 'sum' and sum_supported:
                            res = Obj._read_group(domain, [], [f'{field_name}:{definition.computation_mode}'])
                            new_value = res[0][0] or 0.0

                        else:  # computation mode = count
                            new_value = Obj.search_count(domain)

                        goals_to_write.update(goal._get_write_values(new_value))

            else:
                _logger.error(
                    "Invalid computation mode '%s' in definition %s",
                    definition.computation_mode, definition.name)

            for goal, values in goals_to_write.items():
                if not values:
                    continue
                goal.write(values)
            if self.env.context.get('commit_gamification'):
                self.env.cr.commit()
        return True