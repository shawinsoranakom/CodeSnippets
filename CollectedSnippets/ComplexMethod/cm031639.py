def get_attr_dict(self):
        '''
        Get the PyDictObject ptr representing the attribute dictionary
        (or None if there's a problem)
        '''
        try:
            typeobj = self.type()
            dictoffset = int_from_int(typeobj.field('tp_dictoffset'))
            if dictoffset != 0:
                if dictoffset < 0:
                    if int_from_int(typeobj.field('tp_flags')) & Py_TPFLAGS_MANAGED_DICT:
                        assert dictoffset == -1
                        dictoffset = _managed_dict_offset()
                    else:
                        type_PyVarObject_ptr = gdb.lookup_type('PyVarObject').pointer()
                        tsize = int_from_int(self._gdbval.cast(type_PyVarObject_ptr)['ob_size'])
                        if tsize < 0:
                            tsize = -tsize
                        size = _PyObject_VAR_SIZE(typeobj, tsize)
                        dictoffset += size
                        assert dictoffset % _sizeof_void_p() == 0

                dictptr = self._gdbval.cast(_type_char_ptr()) + dictoffset
                PyObjectPtrPtr = PyObjectPtr.get_gdb_type().pointer()
                dictptr = dictptr.cast(PyObjectPtrPtr)
                if int(dictptr.dereference()) & 1:
                    return None
                return PyObjectPtr.from_pyobject_ptr(dictptr.dereference())
        except RuntimeError:
            # Corrupt data somewhere; fail safe
            pass

        # Not found, or some kind of error:
        return None