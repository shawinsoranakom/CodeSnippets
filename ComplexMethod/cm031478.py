def localcall(self, seq, request):
        self.debug("localcall:", request)
        try:
            how, (oid, methodname, args, kwargs) = request
        except TypeError:
            return ("ERROR", "Bad request format")
        if oid not in self.objtable:
            return ("ERROR", f"Unknown object id: {oid!r}")
        obj = self.objtable[oid]
        if methodname == "__methods__":
            methods = {}
            _getmethods(obj, methods)
            return ("OK", methods)
        if methodname == "__attributes__":
            attributes = {}
            _getattributes(obj, attributes)
            return ("OK", attributes)
        if not hasattr(obj, methodname):
            return ("ERROR", f"Unsupported method name: {methodname!r}")
        method = getattr(obj, methodname)
        try:
            if how == 'CALL':
                ret = method(*args, **kwargs)
                if isinstance(ret, RemoteObject):
                    ret = remoteref(ret)
                return ("OK", ret)
            elif how == 'QUEUE':
                request_queue.put((seq, (method, args, kwargs)))
                return("QUEUED", None)
            else:
                return ("ERROR", "Unsupported message type: %s" % how)
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except OSError:
            raise
        except Exception as ex:
            return ("CALLEXC", ex)
        except:
            msg = "*** Internal Error: rpc.py:SocketIO.localcall()\n\n"\
                  " Object: %s \n Method: %s \n Args: %s\n"
            print(msg % (oid, method, args), file=sys.__stderr__)
            traceback.print_exc(file=sys.__stderr__)
            return ("EXCEPTION", None)