def __eq__(self, other):
        return (
            (self.app_label == other.app_label)
            and (self.name == other.name)
            and (len(self.fields) == len(other.fields))
            and all(
                k1 == k2 and f1.deconstruct()[1:] == f2.deconstruct()[1:]
                for (k1, f1), (k2, f2) in zip(
                    sorted(self.fields.items()),
                    sorted(other.fields.items()),
                )
            )
            and (self.options == other.options)
            and (self.bases == other.bases)
            and (self.managers == other.managers)
        )