def get_path_info(environ):
    """Return the HTTP request's PATH_INFO as a string."""
    path_info = get_bytes_from_wsgi(environ, "PATH_INFO", "/")

    return repercent_broken_unicode(path_info).decode()