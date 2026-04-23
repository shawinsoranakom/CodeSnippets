def units(self):
        "Return a tuple of the units and the name."
        if self.projected or self.local:
            return (self.linear_units, self.linear_name)
        elif self.geographic:
            return (self.angular_units, self.angular_name)
        else:
            return (None, None)