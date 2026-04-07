def get_parent(self, context):
        parent = self.parent_name.resolve(context)
        if not parent:
            error_msg = "Invalid template name in 'extends' tag: %r." % parent
            if self.parent_name.filters or isinstance(self.parent_name.var, Variable):
                error_msg += (
                    " Got this from the '%s' variable." % self.parent_name.token
                )
            raise TemplateSyntaxError(error_msg)
        if isinstance(parent, Template):
            # parent is a django.template.Template
            return parent
        if isinstance(getattr(parent, "template", None), Template):
            # parent is a django.template.backends.django.Template
            return parent.template
        return self.find_template(parent, context)