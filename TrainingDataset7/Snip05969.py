def url_parameters(self):
        from django.contrib.admin.views.main import TO_FIELD_VAR

        params = self.base_url_parameters()
        params.update({TO_FIELD_VAR: self.rel.get_related_field().name})
        return params