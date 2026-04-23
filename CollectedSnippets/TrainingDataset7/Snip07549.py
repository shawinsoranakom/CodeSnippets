def geometry_field(self):
        """
        Return the GeometryField instance associated with the geographic
        column.
        """
        # Use `get_field()` on the model's options so that we
        # get the correct field instance if there's model inheritance.
        opts = self.model._meta
        return opts.get_field(self.geom_field)