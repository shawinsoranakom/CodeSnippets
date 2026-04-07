def get_template(self, template_string):
        return Template(
            template_string.replace("{{% translate ", "{{% {}".format(self.tag_name))
        )