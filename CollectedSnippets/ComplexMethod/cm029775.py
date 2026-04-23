def effective(file, line, frame):
    """Return (active breakpoint, delete temporary flag) or (None, None) as
       breakpoint to act upon.

       The "active breakpoint" is the first entry in bplist[line, file] (which
       must exist) that is enabled, for which checkfuncname is True, and that
       has neither a False condition nor a positive ignore count.  The flag,
       meaning that a temporary breakpoint should be deleted, is False only
       when the condiion cannot be evaluated (in which case, ignore count is
       ignored).

       If no such entry exists, then (None, None) is returned.
    """
    possibles = Breakpoint.bplist[file, line]
    for b in possibles:
        if not b.enabled:
            continue
        if not checkfuncname(b, frame):
            continue
        # Count every hit when bp is enabled
        b.hits += 1
        if not b.cond:
            # If unconditional, and ignoring go on to next, else break
            if b.ignore > 0:
                b.ignore -= 1
                continue
            else:
                # breakpoint and marker that it's ok to delete if temporary
                return (b, True)
        else:
            # Conditional bp.
            # Ignore count applies only to those bpt hits where the
            # condition evaluates to true.
            try:
                val = eval(b.cond, frame.f_globals, frame.f_locals)
                if val:
                    if b.ignore > 0:
                        b.ignore -= 1
                        # continue
                    else:
                        return (b, True)
                # else:
                #   continue
            except:
                # if eval fails, most conservative thing is to stop on
                # breakpoint regardless of ignore count.  Don't delete
                # temporary, as another hint to user.
                return (b, False)
    return (None, None)