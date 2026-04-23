def _check_path(self):
        for action in self:
            if action.path:
                if not re.fullmatch(r'[a-z][a-z0-9_-]*', action.path):
                    raise ValidationError(_('The path should contain only lowercase alphanumeric characters, underscore, and dash, and it should start with a letter.'))
                if action.path.startswith("m-"):
                    raise ValidationError(_("'m-' is a reserved prefix."))
                if action.path.startswith("action-"):
                    raise ValidationError(_("'action-' is a reserved prefix."))
                if action.path == "new":
                    raise ValidationError(_("'new' is reserved, and can not be used as path."))
                # Tables ir_act_window, ir_act_report_xml, ir_act_url, ir_act_server and ir_act_client
                # inherit from table ir_actions (see base_data.sql). The path must be unique across
                # all these tables. The unique constraint is not enough because a big limitation of
                # the inheritance feature is that unique indexes only apply to single tables, and
                # not accross all the tables. So we need to check the uniqueness of the path manually.
                # For more information, see: https://www.postgresql.org/docs/14/ddl-inherit.html#DDL-INHERIT-CAVEATS

                # Note that, we leave the unique constraint in place to check the uniqueness of the path
                # within the same table before checking the uniqueness across all the tables.
                if (self.env['ir.actions.actions'].search_count([('path', '=', action.path)]) > 1):
                    raise ValidationError(_("Path to show in the URL must be unique! Please choose another one."))