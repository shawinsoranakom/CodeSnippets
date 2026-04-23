def get_urls(urls, batchfile, verbose):
    """
    @param verbose      -1: quiet, 0: normal, 1: verbose
    """
    batch_urls = []
    if batchfile is not None:
        try:
            batch_urls = read_batch_urls(
                read_stdin(None if verbose == -1 else 'URLs') if batchfile == '-'
                else open(expand_path(batchfile), encoding='utf-8', errors='ignore'))
            if verbose == 1:
                write_string('[debug] Batch file urls: ' + repr(batch_urls) + '\n')
        except OSError:
            _exit(f'ERROR: batch file {batchfile} could not be read')
    _enc = preferredencoding()
    return [
        url.strip().decode(_enc, 'ignore') if isinstance(url, bytes) else url.strip()
        for url in batch_urls + urls]