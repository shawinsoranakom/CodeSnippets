def render(self, context):
        context[self.variable] = timezone.get_current_timezone_name()
        return ""