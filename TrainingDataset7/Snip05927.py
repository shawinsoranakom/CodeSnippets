def format_callback(obj):
        model = obj.__class__
        opts = obj._meta

        no_edit_link = "%s: %s" % (capfirst(opts.verbose_name), obj)

        if admin_site.is_registered(model):
            if not admin_site.get_model_admin(model).has_delete_permission(
                request, obj
            ):
                perms_needed.add(opts.verbose_name)
            try:
                admin_url = reverse(
                    "%s:%s_%s_change"
                    % (admin_site.name, opts.app_label, opts.model_name),
                    None,
                    (quote(obj.pk),),
                )
            except NoReverseMatch:
                # Change url doesn't exist -- don't display link to edit
                return no_edit_link

            # Display a link to the admin page.
            obj_display = display_for_value(str(obj), EMPTY_VALUE_STRING)
            return format_html(
                '{}: <a href="{}">{}</a>',
                capfirst(opts.verbose_name),
                admin_url,
                obj_display,
            )
        else:
            # Don't display link to edit, because it either has no
            # admin or is edited inline.
            return no_edit_link