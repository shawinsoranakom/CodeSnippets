def _determine_responsible(self, on_demand_responsible, employee):
        if self.plan_id.res_model != 'hr.employee' or self.responsible_type not in {'coach', 'manager', 'employee'}:
            return super()._determine_responsible(on_demand_responsible, employee)
        result = {"error": "", "warning": "", "responsible": False}
        if self.responsible_type == 'coach':
            if not employee.coach_id:
                result['error'] = _('Coach of employee %s is not set.', employee.name)
            result['responsible'] = employee.coach_id.user_id
            if employee.coach_id and not result['responsible']:
                # If a plan cannot be launched due to the coach not being linked to an user,
                # attempt to assign it to the coach's manager user. If that manager is also not linked
                # to an user, continue searching upwards until a manager with a linked user is found.
                # If no one is found still, assign to current user.
                result = self._get_closest_parent_user(
                    employee=employee,
                    responsible=employee.coach_id.parent_id,
                    error_message=_(
                        "The user of %s's coach is not set.", employee.name
                    ),
                )

        elif self.responsible_type == 'manager':
            if not employee.parent_id:
                result['error'] = _('Manager of employee %s is not set.', employee.name)
            result['responsible'] = employee.parent_id.user_id
            if employee.parent_id and not result['responsible']:
                # If a plan cannot be launched due to the manager not being linked to an user,
                # attempt to assign it to the manager's manager user. If that manager is also not linked
                # to an user, continue searching upwards until a manager with a linked user is found.
                # If no one is found still, assign to current user.
                result = self._get_closest_parent_user(
                    employee=employee,
                    responsible=employee.parent_id.parent_id,
                    error_message=_(
                        "The manager of %s should be linked to a user.", employee.name
                    ),
                )

        elif self.responsible_type == 'employee':
            result['responsible'] = employee.user_id
            if not result['responsible']:
                # If a plan cannot be launched due to the employee not being linked to an user,
                # attempt to assign it to the manager's user. If the manager is also not linked
                # to an user, continue searching upwards until a manager with a linked user is found.
                # If no one is found still, assign to current user.
                result = self._get_closest_parent_user(
                    employee=employee,
                    responsible=employee.parent_id,
                    error_message=_(
                        "The employee %s should be linked to a user.", employee.name
                    ),
                )

        if result['error'] or result['responsible']:
            return result