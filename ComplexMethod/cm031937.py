def gen_preprocess_options(macros, include_dirs):
    """Generate C pre-processor options (-D, -U, -I) as used by at least
    two types of compilers: the typical Unix compiler and Visual C++.
    'macros' is the usual thing, a list of 1- or 2-tuples, where (name,)
    means undefine (-U) macro 'name', and (name,value) means define (-D)
    macro 'name' to 'value'.  'include_dirs' is just a list of directory
    names to be added to the header file search path (-I).  Returns a list
    of command-line options suitable for either Unix compilers or Visual
    C++.
    """
    # XXX it would be nice (mainly aesthetic, and so we don't generate
    # stupid-looking command lines) to go over 'macros' and eliminate
    # redundant definitions/undefinitions (ie. ensure that only the
    # latest mention of a particular macro winds up on the command
    # line).  I don't think it's essential, though, since most (all?)
    # Unix C compilers only pay attention to the latest -D or -U
    # mention of a macro on their command line.  Similar situation for
    # 'include_dirs'.  I'm punting on both for now.  Anyways, weeding out
    # redundancies like this should probably be the province of
    # CCompiler, since the data structures used are inherited from it
    # and therefore common to all CCompiler classes.
    pp_opts = []
    for macro in macros:
        if not (isinstance(macro, tuple) and 1 <= len(macro) <= 2):
            raise TypeError(
                  "bad macro definition '%s': "
                  "each element of 'macros' list must be a 1- or 2-tuple"
                  % macro)

        if len(macro) == 1:        # undefine this macro
            pp_opts.append("-U%s" % macro[0])
        elif len(macro) == 2:
            if macro[1] is None:    # define with no explicit value
                pp_opts.append("-D%s" % macro[0])
            else:
                # XXX *don't* need to be clever about quoting the
                # macro value here, because we're going to avoid the
                # shell at all costs when we spawn the command!
                pp_opts.append("-D%s=%s" % macro)

    for dir in include_dirs:
        pp_opts.append("-I%s" % dir)
    return pp_opts