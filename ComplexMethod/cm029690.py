def _get_nargs_pattern(self, action):
        # in all examples below, we have to allow for '--' args
        # which are represented as '-' in the pattern
        nargs = action.nargs
        # if this is an optional action, -- is not allowed
        option = action.option_strings

        # the default (None) is assumed to be a single argument
        if nargs is None:
            nargs_pattern = '([A])' if option else '(-*A-*)'

        # allow zero or one arguments
        elif nargs == OPTIONAL:
            nargs_pattern = '(A?)' if option else '(-*A?-*)'

        # allow zero or more arguments
        elif nargs == ZERO_OR_MORE:
            nargs_pattern = '(A*)' if option else '(-*[A-]*)'

        # allow one or more arguments
        elif nargs == ONE_OR_MORE:
            nargs_pattern = '(A+)' if option else '(-*A[A-]*)'

        # allow any number of options or arguments
        elif nargs == REMAINDER:
            nargs_pattern = '(.*)'

        # allow one argument followed by any number of options or arguments
        elif nargs == PARSER:
            nargs_pattern = '(A[AO]*)' if option else '(-*A[-AO]*)'

        # suppress action, like nargs=0
        elif nargs == SUPPRESS:
            nargs_pattern = '()' if option else '(-*)'

        # all others should be integers
        else:
            nargs_pattern = '([AO]{%d})' % nargs if option else '((?:-*A){%d}-*)' % nargs

        # return the pattern
        return nargs_pattern