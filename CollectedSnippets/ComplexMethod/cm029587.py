def get_argval_argrepr(self, op, arg, offset):
        get_name = None if self.names is None else self.names.__getitem__
        argval = None
        argrepr = ''
        deop = _deoptop(op)
        if arg is not None:
            #  Set argval to the dereferenced value of the argument when
            #  available, and argrepr to the string representation of argval.
            #    _disassemble_bytes needs the string repr of the
            #    raw name index for LOAD_GLOBAL, LOAD_CONST, etc.
            argval = arg
            if deop in hasconst:
                argval, argrepr = _get_const_info(deop, arg, self.co_consts)
            elif deop in hasname:
                if deop == LOAD_GLOBAL:
                    argval, argrepr = _get_name_info(arg//2, get_name)
                    if (arg & 1) and argrepr:
                        argrepr = f"{argrepr} + NULL"
                elif deop == LOAD_ATTR:
                    argval, argrepr = _get_name_info(arg//2, get_name)
                    if (arg & 1) and argrepr:
                        argrepr = f"{argrepr} + NULL|self"
                elif deop == LOAD_SUPER_ATTR:
                    argval, argrepr = _get_name_info(arg//4, get_name)
                    if (arg & 1) and argrepr:
                        argrepr = f"{argrepr} + NULL|self"
                elif deop == IMPORT_NAME:
                    argval, argrepr = _get_name_info(arg//4, get_name)
                    if (arg & 1) and argrepr:
                        argrepr = f"{argrepr} + lazy"
                    elif (arg & 2) and argrepr:
                        argrepr = f"{argrepr} + eager"
                else:
                    argval, argrepr = _get_name_info(arg, get_name)
            elif deop in hasjump or deop in hasexc:
                argval = self.offset_from_jump_arg(op, arg, offset)
                lbl = self.get_label_for_offset(argval)
                assert lbl is not None
                preposition = "from" if deop == END_ASYNC_FOR else "to"
                argrepr = f"{preposition} L{lbl}"
            elif deop in (LOAD_FAST_LOAD_FAST, LOAD_FAST_BORROW_LOAD_FAST_BORROW, STORE_FAST_LOAD_FAST, STORE_FAST_STORE_FAST):
                arg1 = arg >> 4
                arg2 = arg & 15
                val1, argrepr1 = _get_name_info(arg1, self.varname_from_oparg)
                val2, argrepr2 = _get_name_info(arg2, self.varname_from_oparg)
                argrepr = argrepr1 + ", " + argrepr2
                argval = val1, val2
            elif deop in haslocal or deop in hasfree:
                argval, argrepr = _get_name_info(arg, self.varname_from_oparg)
            elif deop in hascompare:
                argval = cmp_op[arg >> 5]
                argrepr = argval
                if arg & 16:
                    argrepr = f"bool({argrepr})"
            elif deop == CONVERT_VALUE:
                argval = (None, str, repr, ascii)[arg]
                argrepr = ('', 'str', 'repr', 'ascii')[arg]
            elif deop == SET_FUNCTION_ATTRIBUTE:
                argrepr = ', '.join(s for i, s in enumerate(FUNCTION_ATTR_FLAGS)
                                    if arg & (1<<i))
            elif deop == BINARY_OP:
                _, argrepr = _nb_ops[arg]
            elif deop == CALL_INTRINSIC_1:
                argrepr = _intrinsic_1_descs[arg]
            elif deop == CALL_INTRINSIC_2:
                argrepr = _intrinsic_2_descs[arg]
            elif deop == LOAD_COMMON_CONSTANT:
                obj = _common_constants[arg]
                if isinstance(obj, type):
                    argrepr = obj.__name__
                else:
                    argrepr = repr(obj)
            elif deop == LOAD_SPECIAL:
                argrepr = _special_method_names[arg]
            elif deop == IS_OP:
                argrepr = 'is not' if argval else 'is'
            elif deop == CONTAINS_OP:
                argrepr = 'not in' if argval else 'in'
        return argval, argrepr