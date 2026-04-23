def _get_obj_does_not_exist_redirect(self, request, opts, object_id):
        """
        Create a message informing the user that the object doesn't exist
        and return a redirect to the admin index page.
        """
        msg = _("%(name)s with ID “%(key)s” doesn’t exist. Perhaps it was deleted?") % {
            "name": opts.verbose_name,
            "key": unquote(object_id),
        }
        self.message_user(request, msg, messages.WARNING)
        url = reverse("admin:index", current_app=self.admin_site.name)
        return HttpResponseRedirect(url)