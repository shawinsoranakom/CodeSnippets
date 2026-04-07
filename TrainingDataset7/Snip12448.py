def aria_describedby(self):
        # Preserve aria-describedby set on the widget.
        if self.field.widget.attrs.get("aria-describedby"):
            return None
        aria_describedby = []
        if self.auto_id and not self.is_hidden:
            if self.help_text:
                aria_describedby.append(f"{self.auto_id}_helptext")
            if self.errors:
                aria_describedby.append(f"{self.auto_id}_error")
        return " ".join(aria_describedby)