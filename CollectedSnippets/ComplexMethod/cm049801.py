def _unlink_except_todo(self):
        master_data = self.browse()
        for xml_id in [xmlid for xmlid, info in self._get_model_info_by_xmlid().items() if info['unlink'] is False]:
            activity_type = self.env.ref(xml_id, raise_if_not_found=False)
            if activity_type and activity_type in self:
                master_data += activity_type
        if master_data:
            raise exceptions.UserError(
                _('You cannot delete %(activity_names)s as it is required in various apps.',
                  activity_names=', '.join(act.name for act in master_data),
            ))