def deserialize(self, value):
                self.deserialize_called += 1
                return GEOSGeometry(value)