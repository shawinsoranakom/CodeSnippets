def label_from_instance(self, obj):
                return ", ".join(c.name for c in obj.colors.all())