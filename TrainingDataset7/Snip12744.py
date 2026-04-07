def __init__(self, media=None, css=None, js=None):
        if media is not None:
            css = getattr(media, "css", {})
            js = getattr(media, "js", [])
        else:
            if css is None:
                css = {}
            if js is None:
                js = []
        self._css_lists = [css]
        self._js_lists = [js]