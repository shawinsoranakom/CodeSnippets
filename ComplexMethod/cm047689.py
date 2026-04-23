def guess_mimetype(bin_data, default=None):
        if isinstance(bin_data, bytearray):
            bin_data = bytes(bin_data[:MIMETYPE_HEAD_SIZE])
        elif not isinstance(bin_data, bytes):
            raise TypeError('`bin_data` must be bytes or bytearray')
        mimetype = magic.from_buffer(bin_data[:MIMETYPE_HEAD_SIZE], mime=True)
        if mimetype in ('application/CDFV2', 'application/x-ole-storage'):
            # Those are the generic file format that Microsoft Office
            # was using before 2006, use our own check to further
            # discriminate the mimetype.
            try:
                if msoffice_mimetype := _check_olecf(bin_data):
                    return msoffice_mimetype
            except Exception:  # noqa: BLE001
                _logger_guess_mimetype.warning(
                    "Sub-checker '_check_olecf' of type '%s' failed",
                    mimetype,
                    exc_info=True,
                )
        if mimetype == 'application/zip':
            # magic doesn't properly detect some Microsoft Office
            # documents created after 2025, use our own check to further
            # discriminate the mimetype.
            # /!\ Only work when bin_data holds the whole zipfile. /!\
            try:
                if msoffice_mimetype := _check_ooxml(bin_data):
                    return msoffice_mimetype
            except zipfile.BadZipFile:
                pass
            except Exception:  # noqa: BLE001
                _logger_guess_mimetype.warning(
                    "Sub-checker '_check_ooxml' of type '%s' failed",
                    mimetype,
                    exc_info=True,
                )
        return mimetype