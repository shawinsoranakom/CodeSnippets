def zip_dir(path, stream, include_dir=True, fnct_sort=None):      # TODO add ignore list
    """
    : param fnct_sort : Function to be passed to "key" parameter of built-in
                        python sorted() to provide flexibility of sorting files
                        inside ZIP archive according to specific requirements.
    """
    path = os.path.normpath(path)
    len_prefix = len(os.path.dirname(path)) if include_dir else len(path)
    if len_prefix:
        len_prefix += 1

    dir_root_path = os.path.realpath(path)
    with zipfile.ZipFile(stream, 'w', compression=zipfile.ZIP_DEFLATED, allowZip64=True) as zipf:
        for dirpath, _dirnames, filenames in os.walk(path):
            filenames = sorted(filenames, key=fnct_sort)
            for fname in filenames:
                bname, ext = os.path.splitext(fname)
                ext = ext or bname
                if ext not in ['.pyc', '.pyo', '.swp', '.DS_Store']:
                    fpath = os.path.normpath(os.path.join(dirpath, fname))
                    real_fpath = os.path.realpath(fpath)
                    if os.path.isfile(real_fpath) and os.path.commonpath([dir_root_path, real_fpath]) == dir_root_path:
                        zipf.write(real_fpath, fpath[len_prefix:])