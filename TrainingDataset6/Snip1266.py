def output():
    return ('\n\nIt seems that there is already a rebase-merge directory, and\n'
            'I wonder if you are in the middle of another rebase.  If that is the\n'
            'case, please try\n'
            '\tgit rebase (--continue | --abort | --skip)\n'
            'If that is not the case, please\n'
            '\trm -fr "/foo/bar/baz/egg/.git/rebase-merge"\n'
            'and run me again.  I am stopping in case you still have something\n'
            'valuable there.\n')