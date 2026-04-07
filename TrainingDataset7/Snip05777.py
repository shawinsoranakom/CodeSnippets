def render_delete_form(self, request, context):
        app_label = self.opts.app_label

        request.current_app = self.admin_site.name
        context.update(
            to_field_var=TO_FIELD_VAR,
            is_popup_var=IS_POPUP_VAR,
            media=self.media,
        )

        return TemplateResponse(
            request,
            self.delete_confirmation_template
            or [
                "admin/{}/{}/delete_confirmation.html".format(
                    app_label, self.opts.model_name
                ),
                "admin/{}/delete_confirmation.html".format(app_label),
                "admin/delete_confirmation.html",
            ],
            context,
        )