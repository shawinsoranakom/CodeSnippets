def __init__(self, tokens, libraries=None, builtins=None, origin=None):
        # Reverse the tokens so delete_first_token(), prepend_token(), and
        # next_token() can operate at the end of the list in constant time.
        self.tokens = list(reversed(tokens))
        self.tags = {}
        self.filters = {}
        self.command_stack = []

        # Custom template tags may store additional data on the parser that
        # will be made available on the template instance. Library authors
        # should use a key to namespace any added data. The 'django' namespace
        # is reserved for internal use.
        self.extra_data = {}

        if libraries is None:
            libraries = {}
        if builtins is None:
            builtins = []

        self.libraries = libraries
        for builtin in builtins:
            self.add_library(builtin)
        self.origin = origin