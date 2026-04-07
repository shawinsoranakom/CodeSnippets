def render(self, context):
        entries = context["log_entries"]
        if self.user is not None:
            user_id = self.user
            if not user_id.isdigit():
                user_id = context[self.user].pk
            entries = entries.filter(user__pk=user_id)
        context[self.varname] = entries[: int(self.limit)]
        return ""