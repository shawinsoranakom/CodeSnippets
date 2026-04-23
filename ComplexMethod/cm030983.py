def close_all(map=None, ignore_all=False):
    if map is None:
        map = socket_map
    for x in list(map.values()):
        try:
            x.close()
        except OSError as x:
            if x.errno == EBADF:
                pass
            elif not ignore_all:
                raise
        except _reraised_exceptions:
            raise
        except:
            if not ignore_all:
                raise
    map.clear()