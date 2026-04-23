def get_context_data(self, **kwargs):
        m_list = [
            m._meta
            for m in apps.get_models()
            if user_has_model_view_permission(self.request.user, m._meta)
        ]
        return super().get_context_data(**{**kwargs, "models": m_list})