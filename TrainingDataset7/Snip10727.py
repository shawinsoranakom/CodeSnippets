def add_restricted_objects(self, field, objs):
        if objs:
            model = objs[0].__class__
            self.restricted_objects[model][field].update(objs)