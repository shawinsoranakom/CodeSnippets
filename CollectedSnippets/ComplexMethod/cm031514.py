def main(del_exitfunc=False):
    """Start the Python execution server in a subprocess

    In the Python subprocess, RPCServer is instantiated with handlerclass
    MyHandler, which inherits register/unregister methods from RPCHandler via
    the mix-in class SocketIO.

    When the RPCServer 'server' is instantiated, the TCPServer initialization
    creates an instance of run.MyHandler and calls its handle() method.
    handle() instantiates a run.Executive object, passing it a reference to the
    MyHandler object.  That reference is saved as attribute rpchandler of the
    Executive instance.  The Executive methods have access to the reference and
    can pass it on to entities that they command
    (e.g. debugger_r.Debugger.start_debugger()).  The latter, in turn, can
    call MyHandler(SocketIO) register/unregister methods via the reference to
    register and unregister themselves.

    """
    global exit_now
    global quitting
    global no_exitfunc
    no_exitfunc = del_exitfunc
    #time.sleep(15) # test subprocess not responding
    try:
        assert(len(sys.argv) > 1)
        port = int(sys.argv[-1])
    except:
        print("IDLE Subprocess: no IP port passed in sys.argv.",
              file=sys.__stderr__)
        return

    capture_warnings(True)
    sys.argv[:] = [""]
    threading.Thread(target=manage_socket,
                     name='SockThread',
                     args=((LOCALHOST, port),),
                     daemon=True,
                    ).start()

    while True:
        try:
            if exit_now:
                try:
                    exit()
                except KeyboardInterrupt:
                    # exiting but got an extra KBI? Try again!
                    continue
            try:
                request = rpc.request_queue.get(block=True, timeout=0.05)
            except queue.Empty:
                request = None
                # Issue 32207: calling handle_tk_events here adds spurious
                # queue.Empty traceback to event handling exceptions.
            if request:
                seq, (method, args, kwargs) = request
                ret = method(*args, **kwargs)
                rpc.response_queue.put((seq, ret))
            else:
                handle_tk_events()
        except KeyboardInterrupt:
            if quitting:
                exit_now = True
            continue
        except SystemExit:
            capture_warnings(False)
            raise
        except:
            type, value, tb = sys.exc_info()
            try:
                print_exception()
                rpc.response_queue.put((seq, None))
            except:
                # Link didn't work, print same exception to __stderr__
                traceback.print_exception(type, value, tb, file=sys.__stderr__)
                exit()
            else:
                continue