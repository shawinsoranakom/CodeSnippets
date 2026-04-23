def assemble_from_fragments(src_path, delimiter=None, compiled_regexp=None, ignore_hidden=False, tmpdir=None):
    """ assemble a file from a directory of fragments """
    tmpfd, temp_path = tempfile.mkstemp(dir=tmpdir)
    tmp = os.fdopen(tmpfd, 'wb')
    delimit_me = False
    add_newline = False
    b_linesep = os.linesep.encode()

    for f in sorted(os.listdir(src_path)):
        if compiled_regexp and not compiled_regexp.search(f):
            continue
        fragment = os.path.join(src_path, f)
        if not os.path.isfile(fragment) or (ignore_hidden and os.path.basename(fragment).startswith('.')):
            continue
        with open(fragment, 'rb') as fragment_fh:
            fragment_content = fragment_fh.read()

        # always put a newline between fragments if the previous fragment didn't end with a newline.
        if add_newline:
            tmp.write(b_linesep)

        # delimiters should only appear between fragments
        if delimit_me:
            if delimiter:
                # un-escape anything like newlines
                delimiter = codecs.escape_decode(delimiter)[0]
                tmp.write(delimiter)
                # always make sure there's a newline after the
                # delimiter, so lines don't run together
                if not delimiter.endswith(b_linesep):
                    tmp.write(b_linesep)

        tmp.write(fragment_content)
        delimit_me = True
        if fragment_content.endswith(b_linesep):
            add_newline = False
        else:
            add_newline = True

    tmp.close()
    return temp_path