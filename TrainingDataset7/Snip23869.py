def get_template_names(self):
        return ["generic_views/book%s.html" % self.template_name_suffix]