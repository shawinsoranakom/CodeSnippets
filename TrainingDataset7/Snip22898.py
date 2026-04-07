def label_tag(self, contents=None, attrs=None, label_suffix=None, tag=None):
        return super().label_tag(
            contents=contents, attrs=attrs, label_suffix="", tag=None
        )