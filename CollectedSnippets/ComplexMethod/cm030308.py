def _check_zipfile(fp):
    try:
        endrec = _EndRecData(fp)
        if endrec:
            if endrec[_ECD_ENTRIES_TOTAL] == 0 and endrec[_ECD_SIZE] == 0 and endrec[_ECD_OFFSET] == 0:
                return True     # Empty zipfiles are still zipfiles
            elif endrec[_ECD_DISK_NUMBER] == endrec[_ECD_DISK_START]:
                # Central directory is on the same disk
                fp.seek(sum(_handle_prepended_data(endrec)))
                if endrec[_ECD_SIZE] >= sizeCentralDir:
                    data = fp.read(sizeCentralDir)   # CD is where we expect it to be
                    if len(data) == sizeCentralDir:
                        centdir = struct.unpack(structCentralDir, data) # CD is the right size
                        if centdir[_CD_SIGNATURE] == stringCentralDir:
                            return True         # First central directory entry  has correct magic number
    except OSError:
        pass
    return False