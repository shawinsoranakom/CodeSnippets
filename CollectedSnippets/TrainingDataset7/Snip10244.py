def __init__(self, model_name, old_name, new_name):
        self.old_name = old_name
        self.new_name = new_name
        super().__init__(model_name, old_name)