def __init__(self, name, app_label):
        self.name = name
        self.app_label = app_label
        # Copy dependencies & other attrs as we might mutate them at runtime
        self.operations = list(self.__class__.operations)
        self.dependencies = list(self.__class__.dependencies)
        self.run_before = list(self.__class__.run_before)
        self.replaces = list(self.__class__.replaces)