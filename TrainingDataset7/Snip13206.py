def resolve(self, context):
        """Resolve this variable against a given context."""
        if self.lookups is not None:
            # We're dealing with a variable that needs to be resolved
            value = self._resolve_lookup(context)
        else:
            # We're dealing with a literal, so it's already been "resolved"
            value = self.literal
        if self.translate:
            is_safe = isinstance(value, SafeData)
            msgid = value.replace("%", "%%")
            msgid = mark_safe(msgid) if is_safe else msgid
            if self.message_context:
                return pgettext_lazy(self.message_context, msgid)
            else:
                return gettext_lazy(msgid)
        return value