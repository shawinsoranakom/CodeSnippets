def instances_with_model(self):
        for model, instances in self.data.items():
            for obj in instances:
                yield model, obj