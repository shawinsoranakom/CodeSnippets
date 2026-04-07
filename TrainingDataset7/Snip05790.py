def _delete_view(self, request, object_id, extra_context):
        "The 'delete' admin view for this model."
        app_label = self.opts.app_label

        to_field = request.POST.get(TO_FIELD_VAR, request.GET.get(TO_FIELD_VAR))
        if to_field and not self.to_field_allowed(request, to_field):
            raise DisallowedModelAdminToField(
                "The field %s cannot be referenced." % to_field
            )

        obj = self.get_object(request, unquote(object_id), to_field)

        if not self.has_delete_permission(request, obj):
            raise PermissionDenied

        if obj is None:
            return self._get_obj_does_not_exist_redirect(request, self.opts, object_id)

        # Populate deleted_objects, a data structure of all related objects
        # that will also be deleted.
        (
            deleted_objects,
            model_count,
            perms_needed,
            protected,
        ) = self.get_deleted_objects([obj], request)

        if request.POST and not protected:  # The user has confirmed the deletion.
            if perms_needed:
                raise PermissionDenied
            obj_display = str(obj)
            attr = str(to_field) if to_field else self.opts.pk.attname
            obj_id = obj.serializable_value(attr)
            self.log_deletions(request, [obj])
            self.delete_model(request, obj)

            return self.response_delete(request, obj_display, obj_id)

        object_name = str(self.opts.verbose_name)

        if perms_needed or protected:
            title = _("Cannot delete %(name)s") % {"name": object_name}
        else:
            title = _("Delete")

        context = {
            **self.admin_site.each_context(request),
            "title": title,
            "subtitle": None,
            "object_name": object_name,
            "object": obj,
            "escaped_object": display_for_value(str(obj), EMPTY_VALUE_STRING),
            "deleted_objects": deleted_objects,
            "model_count": dict(model_count).items(),
            "perms_lacking": perms_needed,
            "protected": protected,
            "opts": self.opts,
            "app_label": app_label,
            "preserved_filters": self.get_preserved_filters(request),
            "is_popup": IS_POPUP_VAR in request.POST or IS_POPUP_VAR in request.GET,
            "to_field": to_field,
            **(extra_context or {}),
        }

        return self.render_delete_form(request, context)