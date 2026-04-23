def user_change_password(self, request, id, form_url=""):
        user = self.get_object(request, unquote(id))
        if not self.has_change_permission(request, user):
            raise PermissionDenied
        if user is None:
            raise Http404(
                _("%(name)s object with primary key %(key)r does not exist.")
                % {
                    "name": self.opts.verbose_name,
                    "key": escape(id),
                }
            )
        if request.method == "POST":
            form = self.change_password_form(user, request.POST)
            if form.is_valid():
                # If disabling password-based authentication was requested
                # (via the form field `usable_password`), the submit action
                # must be "unset-password". This check is most relevant when
                # the admin user has two submit buttons available (for example
                # when Javascript is disabled).
                valid_submission = (
                    form.cleaned_data["set_usable_password"]
                    or "unset-password" in request.POST
                )
                if not valid_submission:
                    msg = gettext("Conflicting form data submitted. Please try again.")
                    messages.error(request, msg)
                    return HttpResponseRedirect(request.get_full_path())

                user = form.save()
                change_message = self.construct_change_message(request, form, None)
                self.log_change(request, user, change_message)
                if user.has_usable_password():
                    msg = gettext("Password changed successfully.")
                else:
                    msg = gettext("Password-based authentication was disabled.")
                messages.success(request, msg)
                update_session_auth_hash(request, form.user)
                return HttpResponseRedirect(
                    reverse(
                        "%s:%s_%s_change"
                        % (
                            self.admin_site.name,
                            user._meta.app_label,
                            user._meta.model_name,
                        ),
                        args=(user.pk,),
                    )
                )
        else:
            form = self.change_password_form(user)

        fieldsets = [(None, {"fields": list(form.base_fields)})]
        admin_form = admin.helpers.AdminForm(form, fieldsets, {})

        if user.has_usable_password():
            title = _("Change password: %s")
        else:
            title = _("Set password: %s")
        context = {
            "title": title % escape(user.get_username()),
            "adminForm": admin_form,
            "form_url": form_url,
            "form": form,
            "is_popup": (IS_POPUP_VAR in request.POST or IS_POPUP_VAR in request.GET),
            "is_popup_var": IS_POPUP_VAR,
            "add": True,
            "change": False,
            "has_delete_permission": False,
            "has_change_permission": True,
            "has_absolute_url": False,
            "opts": self.opts,
            "original": user,
            "save_as": False,
            "show_save": True,
            **self.admin_site.each_context(request),
        }

        request.current_app = self.admin_site.name

        return TemplateResponse(
            request,
            self.change_user_password_template
            or "admin/auth/user/change_password.html",
            context,
        )