def _EndRecData64(fpin, offset, endrec):
    """
    Read the ZIP64 end-of-archive records and use that to update endrec
    """
    offset -= sizeEndCentDir64Locator
    if offset < 0:
        # The file is not large enough to contain a ZIP64
        # end-of-archive record, so just return the end record we were given.
        return endrec
    fpin.seek(offset)
    data = fpin.read(sizeEndCentDir64Locator)
    if len(data) != sizeEndCentDir64Locator:
        raise OSError("Unknown I/O error")
    sig, diskno, reloff, disks = struct.unpack(structEndArchive64Locator, data)
    if sig != stringEndArchive64Locator:
        return endrec

    if diskno != 0 or disks > 1:
        raise BadZipFile("zipfiles that span multiple disks are not supported")

    offset -= sizeEndCentDir64
    if reloff > offset:
        raise BadZipFile("Corrupt zip64 end of central directory locator")
    # First, check the assumption that there is no prepended data.
    fpin.seek(reloff)
    extrasz = offset - reloff
    data = fpin.read(sizeEndCentDir64)
    if len(data) != sizeEndCentDir64:
        raise OSError("Unknown I/O error")
    if not data.startswith(stringEndArchive64) and reloff != offset:
        # Since we already have seen the Zip64 EOCD Locator, it's
        # possible we got here because there is prepended data.
        # Assume no 'zip64 extensible data'
        fpin.seek(offset)
        extrasz = 0
        data = fpin.read(sizeEndCentDir64)
        if len(data) != sizeEndCentDir64:
            raise OSError("Unknown I/O error")
    if not data.startswith(stringEndArchive64):
        raise BadZipFile("Zip64 end of central directory record not found")

    sig, sz, create_version, read_version, disk_num, disk_dir, \
        dircount, dircount2, dirsize, diroffset = \
        struct.unpack(structEndArchive64, data)
    if (diroffset + dirsize != reloff or
        sz + 12 != sizeEndCentDir64 + extrasz):
        raise BadZipFile("Corrupt zip64 end of central directory record")

    # Update the original endrec using data from the ZIP64 record
    endrec[_ECD_SIGNATURE] = sig
    endrec[_ECD_DISK_NUMBER] = disk_num
    endrec[_ECD_DISK_START] = disk_dir
    endrec[_ECD_ENTRIES_THIS_DISK] = dircount
    endrec[_ECD_ENTRIES_TOTAL] = dircount2
    endrec[_ECD_SIZE] = dirsize
    endrec[_ECD_OFFSET] = diroffset
    endrec[_ECD_LOCATION] = offset - extrasz
    return endrec