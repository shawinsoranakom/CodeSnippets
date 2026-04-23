def tuple(self):
        "Return the tuple of this point."
        if self.is_3d and self.is_measured:
            return self.x, self.y, self.z, self.m
        if self.is_3d:
            return self.x, self.y, self.z
        if self.is_measured:
            return self.x, self.y, self.m
        return self.x, self.y