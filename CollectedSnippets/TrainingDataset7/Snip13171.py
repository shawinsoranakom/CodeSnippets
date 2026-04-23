def get_exception_info(self, exception, token):
        template = self.origin.loader.get_template(self.origin.template_name)
        return template.get_exception_info(exception, token)