def get_file_content(path, default=None, strip=True):
    """
        Return the contents of a given file path

        :args path: path to file to return contents from
        :args default: value to return if we could not read file
        :args strip: controls if we strip whitespace from the result or not

        :returns: String with file contents (optionally stripped) or 'default' value
    """
    data = default
    if os.path.exists(path) and os.access(path, os.R_OK):
        datafile = None
        try:
            datafile = open(path)
            try:
                # try to not enter kernel 'block' mode, which prevents timeouts
                fd = datafile.fileno()
                flag = fcntl.fcntl(fd, fcntl.F_GETFL)
                fcntl.fcntl(fd, fcntl.F_SETFL, flag | os.O_NONBLOCK)
            except Exception:
                pass  # not required to operate, but would have been nice!

            # actually read the data
            data = datafile.read()

            if strip:
                data = data.strip()

            if len(data) == 0:
                data = default

        except Exception:
            # ignore errors as some jails/containers might have readable permissions but not allow reads
            pass
        finally:
            if datafile is not None:
                datafile.close()

    return data