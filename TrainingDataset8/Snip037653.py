def __init__(self, *args):
        super(StreamlitAPIWarning, self).__init__(*args)
        import inspect
        import traceback

        f = inspect.currentframe()
        self.tacked_on_stack = traceback.extract_stack(f)