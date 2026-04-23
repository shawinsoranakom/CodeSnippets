def _compute_activity_info(self):
        to_reset = self.filtered(lambda act: not act.model_id or act.state != 'next_activity')
        if to_reset:
            to_reset.activity_type_id = False
            to_reset.activity_summary = False
            to_reset.activity_note = False
            to_reset.activity_date_deadline_range = False
            to_reset.activity_date_deadline_range_type = False
            to_reset.activity_user_type = False
        for action in (self - to_reset):
            if action.activity_type_id.res_model and action.model_id.model != action.activity_type_id.res_model:
                action.activity_type_id = False
            if not action.activity_summary:
                action.activity_summary = action.activity_type_id.summary
            if not action.activity_date_deadline_range_type:
                action.activity_date_deadline_range_type = 'days'
            if not action.activity_user_type:
                action.activity_user_type = 'specific'