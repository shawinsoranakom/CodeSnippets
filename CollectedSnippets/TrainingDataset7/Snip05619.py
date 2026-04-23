def field_admin_ordering(self, field, request, model_admin):
        """
        Return the model admin's ordering for related field, if provided.
        """
        try:
            related_admin = model_admin.admin_site.get_model_admin(
                field.remote_field.model
            )
        except NotRegistered:
            return ()
        else:
            return related_admin.get_ordering(request)