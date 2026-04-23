def __init__(self, attrs=None):
        if (
            attrs is not None
            and not self.allow_multiple_selected
            and attrs.get("multiple", False)
        ):
            raise ValueError(
                "%s doesn't support uploading multiple files."
                % self.__class__.__qualname__
            )
        if self.allow_multiple_selected:
            if attrs is None:
                attrs = {"multiple": True}
            else:
                attrs.setdefault("multiple", True)
        super().__init__(attrs)