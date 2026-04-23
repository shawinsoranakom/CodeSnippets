def print_traceback_helper(full_info):
    frame = Frame.get_selected_python_frame()
    interp_frame = PyFramePtr.get_thread_local_frame()
    if not frame and not interp_frame:
        print('Unable to locate python frame')
        return

    sys.stdout.write('Traceback (most recent call first):\n')
    if frame:
        while frame:
            frame_index = frame.get_index() if full_info else None
            if frame.is_evalframe():
                pyop = frame.get_pyop()
                if pyop is not None:
                    # Use the _PyInterpreterFrame from the gdb frame
                    interp_frame = pyop
                if interp_frame:
                    interp_frame = interp_frame.print_traceback_until_shim(frame_index)
                else:
                    sys.stdout.write('  (unable to read python frame information)\n')
            else:
                info = frame.is_other_python_frame()
                if full_info:
                    if info:
                        sys.stdout.write('#%i %s\n' % (frame_index, info))
                elif info:
                    sys.stdout.write('  %s\n' % info)
            frame = frame.older()
    else:
        # Fall back to just using the thread-local frame
        while interp_frame:
            interp_frame = interp_frame.print_traceback_until_shim()