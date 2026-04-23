def to_stylesheet(s):
            return s if isinstance(s, Stylesheet) else Stylesheet(s)