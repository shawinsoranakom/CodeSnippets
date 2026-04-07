def _format_names(self, objs):
        """App label/class name interpolation for object names."""
        names = {"app_label": self.app_label.lower(), "class": self.model_name}
        new_objs = []
        for obj in objs:
            obj = obj.clone()
            obj.name %= names
            new_objs.append(obj)
        return new_objs