def _is_thread_message(self, vals=False, thread=None):
        """ Tool method to compute thread validity in notification methods. """
        vals = vals or {}
        res_model = vals['model'] if 'model' in vals else thread._name if thread else self.model
        res_id = vals['res_id'] if 'res_id' in vals else thread.ids[0] if thread and thread.ids else self.res_id
        return bool(res_id) if (res_model and res_model != 'mail.thread') else False