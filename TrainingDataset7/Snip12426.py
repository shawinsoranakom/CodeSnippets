def __bool__(self):
        # BoundField evaluates to True even if it doesn't have subwidgets.
        return True