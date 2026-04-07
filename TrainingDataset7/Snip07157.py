def name(self):
        "Return the name of this Spatial Reference."
        if self.projected:
            return self.attr_value("PROJCS")
        elif self.geographic:
            return self.attr_value("GEOGCS")
        elif self.local:
            return self.attr_value("LOCAL_CS")
        else:
            return None