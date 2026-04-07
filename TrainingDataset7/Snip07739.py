def value_from_datadict(self, data, files, name):
        return [
            self.widget.value_from_datadict(data, files, "%s_%s" % (name, index))
            for index in range(self.size)
        ]