def readwrite(obj, flags):
    try:
        if flags & select.POLLIN:
            obj.handle_read_event()
        if flags & select.POLLOUT:
            obj.handle_write_event()
        if flags & select.POLLPRI:
            obj.handle_expt_event()
        if flags & (select.POLLHUP | select.POLLERR | select.POLLNVAL):
            obj.handle_close()
    except OSError as e:
        if e.errno not in _DISCONNECTED:
            obj.handle_error()
        else:
            obj.handle_close()
    except _reraised_exceptions:
        raise
    except:
        obj.handle_error()