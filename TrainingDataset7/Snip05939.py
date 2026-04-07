def has_perm(self, request, obj=None):
        """Check if user has permission to access the related model."""
        return self.model_admin.has_view_permission(request, obj=obj)