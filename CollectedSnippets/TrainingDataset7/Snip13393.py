def render(self, context):
        from django.utils.html import strip_spaces_between_tags

        return strip_spaces_between_tags(self.nodelist.render(context).strip())