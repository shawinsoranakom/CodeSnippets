def id_for_label(self):
        """
        Wrapper around the field widget's `id_for_label` method.
        Useful, for example, for focusing on this field regardless of whether
        it has a single widget or a MultiWidget.
        """
        widget = self.field.widget
        id_ = widget.attrs.get("id") or self.auto_id
        return widget.id_for_label(id_)