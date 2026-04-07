def get_template(self, template_string):
        return Template(
            template_string.replace(
                "{{% blocktranslate ", "{{% {}".format(self.tag_name)
            ).replace(
                "{{% endblocktranslate %}}", "{{% end{} %}}".format(self.tag_name)
            )
        )