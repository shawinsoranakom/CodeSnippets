def __init__(self, wrapper):
        """
        wrapper is a database wrapper.

        It must have a Database attribute defining PEP-249 exceptions.
        """
        self.wrapper = wrapper