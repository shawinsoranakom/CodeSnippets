def _compute_error(self):
        for scheduler in self:
            errors = set()
            warnings = set()
            if scheduler.res_model:
                applied_on = scheduler._get_applied_on_records()
                if applied_on and ('company_id' in scheduler.env[applied_on._name]._fields and
                                len(applied_on.mapped('company_id')) > 1):
                    errors.add(_('The records must belong to the same company.'))
            if scheduler.plan_id:
                errors |= set(scheduler._check_plan_templates_error(applied_on))
                warnings |= set(scheduler._check_plan_templates_warning(applied_on))
                if not scheduler.res_ids:
                    errors.add(_("Can't launch a plan without a record."))
            if not scheduler.res_ids and not scheduler.activity_user_id:
                errors.add(_("Can't schedule activities without either a record or a user."))
            if errors:
                error_header = (
                    _('The plan "%(plan_name)s" cannot be launched:', plan_name=scheduler.plan_id.name) if scheduler.plan_id
                    else _('The activity cannot be launched:')
                )
                error_body = Markup('<ul>%s</ul>') % (
                    Markup().join(Markup('<li>%s</li>') % error for error in errors)
                )
                scheduler.error = f'{error_header}{error_body}'
                scheduler.has_error = True
                scheduler.has_warning = False
            else:
                scheduler.error = False
                scheduler.has_error = False

            if warnings:
                warning_header = (
                    _('The plan "%(plan_name)s" can be launched, with these additional effects:', plan_name=scheduler.plan_id.name) if scheduler.plan_id
                    else _('The activity can be launched, with these additional effects:')
                )
                warning_body = Markup('<ul>%s</ul>') % (
                    Markup().join(Markup('<li>%s</li>') % warning for warning in warnings)
                )
                scheduler.warning = f'{warning_header}{warning_body}'
                scheduler.has_warning = True
            else:
                scheduler.warning = False
                scheduler.has_warning = False