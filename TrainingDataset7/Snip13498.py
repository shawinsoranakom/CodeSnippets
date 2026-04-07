def get_template_sources(self, template_name):
        yield Origin(
            name=template_name,
            template_name=template_name,
            loader=self,
        )