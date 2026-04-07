def get_admin_url(self):
        """
        Return the admin URL to edit the object represented by this log entry.
        """
        if self.content_type and self.object_id:
            url_name = "admin:%s_%s_change" % (
                self.content_type.app_label,
                self.content_type.model,
            )
            try:
                return reverse(url_name, args=(quote(self.object_id),))
            except NoReverseMatch:
                pass
        return None