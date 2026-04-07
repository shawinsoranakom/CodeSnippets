def get_extra_descriptor_filter(self, instance):
        return models.Q(lang=get_language())