def __init__(
        self,
        widget,
        rel,
        admin_site,
        can_add_related=None,
        can_change_related=False,
        can_delete_related=False,
        can_view_related=False,
    ):
        self.needs_multipart_form = widget.needs_multipart_form
        self.attrs = widget.attrs
        self.widget = widget
        self.rel = rel
        # Backwards compatible check for whether a user can add related
        # objects.
        if can_add_related is None:
            can_add_related = admin_site.is_registered(rel.model)
        self.can_add_related = can_add_related
        if not isinstance(widget, AutocompleteMixin):
            self.attrs["data-context"] = "available-source"
        # Only single-select Select widgets are supported.
        supported = not getattr(
            widget, "allow_multiple_selected", False
        ) and isinstance(widget, Select)
        self.can_change_related = supported and can_change_related
        # XXX: The deletion UX can be confusing when dealing with cascading
        # deletion.
        cascade = getattr(rel, "on_delete", None) is CASCADE
        self.can_delete_related = supported and not cascade and can_delete_related
        self.can_view_related = supported and can_view_related
        # To check if the related object is registered with this AdminSite.
        self.admin_site = admin_site
        self.use_fieldset = widget.use_fieldset