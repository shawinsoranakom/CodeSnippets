def value_to_string(self, obj):
        qs = getattr(obj, self.name).all()
        return str([instance.pk for instance in qs])