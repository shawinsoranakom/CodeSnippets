def startElement(self, name, attrs):
        # Sort attrs for a deterministic output.
        sorted_attrs = dict(sorted(attrs.items())) if attrs else attrs
        super().startElement(name, sorted_attrs)