def get_template(self, template_name):
        try:
            return Template(self.env.get_template(template_name), self)
        except jinja2.TemplateNotFound as exc:
            raise TemplateDoesNotExist(exc.name, backend=self) from exc
        except jinja2.TemplateSyntaxError as exc:
            new = TemplateSyntaxError(exc.args)
            new.template_debug = get_exception_info(exc)
            raise new from exc