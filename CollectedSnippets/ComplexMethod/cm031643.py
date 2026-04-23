def is_other_python_frame(self):
        '''Is this frame worth displaying in python backtraces?
        Examples:
          - waiting on the GIL
          - garbage-collecting
          - within a CFunction
         If it is, return a descriptive string
         For other frames, return False
         '''
        if self.is_waiting_for_gil():
            return 'Waiting for the GIL'

        if self.is_gc_collect():
            return 'Garbage-collecting'

        # Detect invocations of PyCFunction instances:
        frame = self._gdbframe
        caller = frame.name()
        if not caller:
            return False

        if (caller.startswith('cfunction_vectorcall_') or
            caller == 'cfunction_call'):
            arg_name = 'func'
            # Within that frame:
            #   "func" is the local containing the PyObject* of the
            # PyCFunctionObject instance
            #   "f" is the same value, but cast to (PyCFunctionObject*)
            #   "self" is the (PyObject*) of the 'self'
            try:
                # Use the prettyprinter for the func:
                func = frame.read_var(arg_name)
                return str(func)
            except ValueError:
                return ('PyCFunction invocation (unable to read %s: '
                        'missing debuginfos?)' % arg_name)
            except RuntimeError:
                return 'PyCFunction invocation (unable to read %s)' % arg_name

        if caller == 'wrapper_call':
            arg_name = 'wp'
            try:
                func = frame.read_var(arg_name)
                return str(func)
            except ValueError:
                return ('<wrapper_call invocation (unable to read %s: '
                        'missing debuginfos?)>' % arg_name)
            except RuntimeError:
                return '<wrapper_call invocation (unable to read %s)>' % arg_name

        # This frame isn't worth reporting:
        return False