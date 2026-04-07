def template_name(self):
        if "template_name" in self.data:
            return self.data["template_name"]
        return self.parent_widget.template_name