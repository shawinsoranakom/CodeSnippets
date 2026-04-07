def widget_type(self):
        return re.sub(
            r"widget$|input$", "", self.field.widget.__class__.__name__.lower()
        )