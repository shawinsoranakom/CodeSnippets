def do_related_class(self, other, cls):
        self.set_attributes_from_rel()
        self.contribute_to_related_class(other, self.remote_field)