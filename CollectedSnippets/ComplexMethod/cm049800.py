def write(self, vals):
        # Protect some master types against model change when they are used
        # as default in apps, in business flows, plans, ...
        if 'res_model' in vals:
            xmlid_to_model = {
                xmlid: info['res_model']
                for xmlid, info in self._get_model_info_by_xmlid().items()
            }
            modified = self.browse()
            for xml_id, model in xmlid_to_model.items():
                activity_type = self.env.ref(xml_id, raise_if_not_found=False)
                # beware '' and False for void res_model
                if activity_type and (vals['res_model'] or False) != (model or False) and activity_type in self:
                    modified += activity_type
            if modified:
                raise exceptions.UserError(
                    _('You cannot modify %(activities_names)s target model as they are are required in various apps.',
                      activities_names=', '.join(act.name for act in modified),
                ))
        return super().write(vals)