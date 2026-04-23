def response_add(self, request, obj, post_url_continue=None):
        """
        Determine the HttpResponse for the add_view stage.
        """
        opts = obj._meta
        preserved_filters = self.get_preserved_filters(request)
        preserved_qsl = self._get_preserved_qsl(request, preserved_filters)
        obj_url = reverse(
            "admin:%s_%s_change" % (opts.app_label, opts.model_name),
            args=(quote(obj.pk),),
            current_app=self.admin_site.name,
        )
        # Add a link to the object's change form if the user can edit the obj.
        obj_display = display_for_value(str(obj), EMPTY_VALUE_STRING)
        if self.has_change_permission(request, obj):
            obj_repr = format_html(
                '<a href="{}">{}</a>', urlquote(obj_url), obj_display
            )
        else:
            obj_repr = obj_display
        msg_dict = {
            "name": opts.verbose_name,
            "obj": obj_repr,
        }
        # Here, we distinguish between different save types by checking for
        # the presence of keys in request.POST.

        if IS_POPUP_VAR in request.POST:
            to_field = request.POST.get(TO_FIELD_VAR)
            if to_field:
                attr = str(to_field)
            else:
                attr = obj._meta.pk.attname
            value = obj.serializable_value(attr)
            popup_response = {
                "value": str(value),
                "obj": str(obj),
            }

            # Find the optgroup for the new item, if available
            source_model_name = request.POST.get(SOURCE_MODEL_VAR)
            source_admin = None
            if source_model_name:
                app_label, model_name = source_model_name.split(".", 1)
                try:
                    source_model = apps.get_model(app_label, model_name)
                except LookupError:
                    msg = _('The app "%s" could not be found.') % source_model_name
                    self.message_user(request, msg, messages.ERROR)
                else:
                    source_admin = self.admin_site._registry.get(source_model)

            if source_admin:
                form = source_admin.get_form(request)()
                if self.opts.verbose_name_plural in form.fields:
                    field = form.fields[self.opts.verbose_name_plural]
                    for option_value, option_label in field.choices:
                        # Check if this is an optgroup (label is a sequence
                        # of choices rather than a single string value).
                        if isinstance(option_label, (list, tuple)):
                            # It's an optgroup:
                            # (group_name, [(value, label), ...])
                            optgroup_label = option_value
                            for choice_value, choice_display in option_label:
                                if choice_display == str(obj):
                                    popup_response["optgroup"] = str(optgroup_label)
                                    break

            popup_response_data = json.dumps(popup_response)
            return TemplateResponse(
                request,
                self.popup_response_template
                or [
                    "admin/%s/%s/popup_response.html"
                    % (opts.app_label, opts.model_name),
                    "admin/%s/popup_response.html" % opts.app_label,
                    "admin/popup_response.html",
                ],
                {
                    "popup_response_data": popup_response_data,
                },
            )

        elif "_continue" in request.POST or (
            # Redirecting after "Save as new".
            "_saveasnew" in request.POST
            and self.save_as_continue
            and self.has_change_permission(request, obj)
        ):
            msg = _("The {name} “{obj}” was added successfully.")
            if self.has_change_permission(request, obj):
                msg += " " + _("You may edit it again below.")
            self.message_user(request, format_html(msg, **msg_dict), messages.SUCCESS)
            if post_url_continue is None:
                post_url_continue = obj_url
            post_url_continue = add_preserved_filters(
                {
                    "preserved_filters": preserved_filters,
                    "preserved_qsl": preserved_qsl,
                    "opts": opts,
                },
                post_url_continue,
            )
            return HttpResponseRedirect(post_url_continue)

        elif "_addanother" in request.POST:
            msg = format_html(
                _(
                    "The {name} “{obj}” was added successfully. You may add another "
                    "{name} below."
                ),
                **msg_dict,
            )
            self.message_user(request, msg, messages.SUCCESS)
            redirect_url = request.path
            redirect_url = add_preserved_filters(
                {
                    "preserved_filters": preserved_filters,
                    "preserved_qsl": preserved_qsl,
                    "opts": opts,
                },
                redirect_url,
            )
            return HttpResponseRedirect(redirect_url)

        else:
            msg = format_html(
                _("The {name} “{obj}” was added successfully."), **msg_dict
            )
            self.message_user(request, msg, messages.SUCCESS)
            return self.response_post_save_add(request, obj)