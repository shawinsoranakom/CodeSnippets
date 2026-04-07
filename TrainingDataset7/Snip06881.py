def __str__(self):
        "Return OGR GetName and Driver for the Data Source."
        return "%s (%s)" % (self.name, self.driver)