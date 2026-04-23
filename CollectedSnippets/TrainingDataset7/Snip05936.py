def get_paginator(self, *args, **kwargs):
        """Use the ModelAdmin's paginator."""
        return self.model_admin.get_paginator(self.request, *args, **kwargs)