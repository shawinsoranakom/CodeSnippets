def _instanciate_attrs(self, model_data):
        attrs = super()._instanciate_attrs(model_data)
        if model_data.get('is_mail_blacklist') and attrs['_name'] != 'mail.thread.blacklist':
            parents = attrs.get('_inherit') or []
            parents = [parents] if isinstance(parents, str) else parents
            attrs['_inherit'] = parents + ['mail.thread.blacklist']
            if attrs['_custom']:
                attrs['_primary_email'] = 'x_email'
        elif model_data.get('is_mail_thread') and attrs['_name'] != 'mail.thread':
            parents = attrs.get('_inherit') or []
            parents = [parents] if isinstance(parents, str) else parents
            attrs['_inherit'] = parents + ['mail.thread']
        if model_data.get('is_mail_activity') and attrs['_name'] != 'mail.activity.mixin':
            parents = attrs.get('_inherit') or []
            parents = [parents] if isinstance(parents, str) else parents
            attrs['_inherit'] = parents + ['mail.activity.mixin']
        return attrs