def add_prefix(self, field_name):
                return (
                    "%s-prefix-%s" % (self.prefix, field_name)
                    if self.prefix
                    else field_name
                )