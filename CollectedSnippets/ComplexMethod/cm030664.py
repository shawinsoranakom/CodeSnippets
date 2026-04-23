def info_breakpoints():
    bp_list = [bp for  bp in _bdb.Breakpoint.bpbynumber if bp]
    if not bp_list:
        return ''

    header_added = False
    for bp in bp_list:
        if not header_added:
            info = 'BpNum Temp Enb Hits Ignore Where\n'
            header_added = True

        disp = 'yes ' if bp.temporary else 'no  '
        enab = 'yes' if bp.enabled else 'no '
        info += ('%-5d %s %s %-4d %-6d at %s:%d' %
                    (bp.number, disp, enab, bp.hits, bp.ignore,
                     os.path.basename(bp.file), bp.line))
        if bp.cond:
            info += '\n\tstop only if %s' % (bp.cond,)
        info += '\n'
    return info