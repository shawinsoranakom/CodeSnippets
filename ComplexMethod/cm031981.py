def _iter_ignored(infile, relroot):
    if relroot and relroot is not fsutil.USE_CWD:
        relroot = os.path.abspath(relroot)
    bogus = {_tables.EMPTY, _tables.UNKNOWN}
    for row in _tables.read_table(infile, IGNORED_HEADER, sep='\t'):
        *varidinfo, reason = row
        if _tables.EMPTY in varidinfo or _tables.UNKNOWN in varidinfo:
            varidinfo = tuple(None if v in bogus else v
                              for v in varidinfo)
        if reason in bogus:
            reason = None
        try:
            varid = _info.DeclID.from_row(varidinfo)
        except BaseException as e:
            e.add_note(f"Error occurred when processing row {varidinfo} in {infile}.")
            e.add_note(f"Could it be that you added a row which is not tab-delimited?")
            raise e
        varid = varid.fix_filename(relroot, formatted=False, fixroot=False)
        yield varid, reason