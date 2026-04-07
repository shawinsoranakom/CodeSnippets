def write_wrapper(data):
            called_threads.append(threading.current_thread())
            return original_write(data)