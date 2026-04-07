def label_tag(self, contents=None, attrs=None, label_suffix=None, tag=None):
        attrs = attrs or {}
        attrs["class"] = "custom-class"
        return super().label_tag(contents, attrs, label_suffix, tag)