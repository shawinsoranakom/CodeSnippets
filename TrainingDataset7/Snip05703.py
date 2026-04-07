def get_field_queryset(self, db, db_field, request):
        """
        If the ModelAdmin specifies ordering, the queryset should respect that
        ordering. Otherwise don't specify the queryset, let the field decide
        (return None in that case).
        """
        try:
            related_admin = self.admin_site.get_model_admin(db_field.remote_field.model)
        except NotRegistered:
            return None
        else:
            ordering = related_admin.get_ordering(request)
            if ordering is not None and ordering != ():
                return db_field.remote_field.model._default_manager.using(db).order_by(
                    *ordering
                )
        return None