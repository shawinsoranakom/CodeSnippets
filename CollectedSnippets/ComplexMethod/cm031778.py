def _r_object(self) -> Any:
        code = self.r_byte()
        flag = code & FLAG_REF
        type = code & ~FLAG_REF
        # print("  "*self.level + f"{code} {flag} {type} {chr(type)!r}")
        self.level += 1

        def R_REF(obj: Any) -> Any:
            if flag:
                obj = self.r_ref(obj, flag)
            return obj

        if type == Type.NULL:
            return NULL
        elif type == Type.NONE:
            return None
        elif type == Type.ELLIPSIS:
            return Ellipsis
        elif type == Type.FALSE:
            return False
        elif type == Type.TRUE:
            return True
        elif type == Type.INT:
            return R_REF(self.r_long())
        elif type == Type.INT64:
            return R_REF(self.r_long64())
        elif type == Type.LONG:
            return R_REF(self.r_PyLong())
        elif type == Type.FLOAT:
            return R_REF(self.r_float_str())
        elif type == Type.BINARY_FLOAT:
            return R_REF(self.r_float_bin())
        elif type == Type.COMPLEX:
            return R_REF(complex(self.r_float_str(),
                                    self.r_float_str()))
        elif type == Type.BINARY_COMPLEX:
            return R_REF(complex(self.r_float_bin(),
                                    self.r_float_bin()))
        elif type == Type.STRING:
            n = self.r_long()
            return R_REF(self.r_string(n))
        elif type == Type.ASCII_INTERNED or type == Type.ASCII:
            n = self.r_long()
            return R_REF(self.r_string(n).decode("ascii"))
        elif type == Type.SHORT_ASCII_INTERNED or type == Type.SHORT_ASCII:
            n = self.r_byte()
            return R_REF(self.r_string(n).decode("ascii"))
        elif type == Type.INTERNED or type == Type.UNICODE:
            n = self.r_long()
            return R_REF(self.r_string(n).decode("utf8", "surrogatepass"))
        elif type == Type.SMALL_TUPLE:
            n = self.r_byte()
            idx = self.r_ref_reserve(flag)
            retval: Any = tuple(self.r_object() for _ in range(n))
            self.r_ref_insert(retval, idx, flag)
            return retval
        elif type == Type.TUPLE:
            n = self.r_long()
            idx = self.r_ref_reserve(flag)
            retval = tuple(self.r_object() for _ in range(n))
            self.r_ref_insert(retval, idx, flag)
            return retval
        elif type == Type.LIST:
            n = self.r_long()
            retval = R_REF([])
            for _ in range(n):
                retval.append(self.r_object())
            return retval
        elif type == Type.DICT:
            retval = R_REF({})
            while True:
                key = self.r_object()
                if key == NULL:
                    break
                val = self.r_object()
                retval[key] = val
            return retval
        elif type == Type.SET:
            n = self.r_long()
            retval = R_REF(set())
            for _ in range(n):
                v = self.r_object()
                retval.add(v)
            return retval
        elif type == Type.FROZENSET:
            n = self.r_long()
            s: set[Any] = set()
            idx = self.r_ref_reserve(flag)
            for _ in range(n):
                v = self.r_object()
                s.add(v)
            retval = frozenset(s)
            self.r_ref_insert(retval, idx, flag)
            return retval
        elif type == Type.CODE:
            retval = R_REF(Code())
            retval.co_argcount = self.r_long()
            retval.co_posonlyargcount = self.r_long()
            retval.co_kwonlyargcount = self.r_long()
            retval.co_stacksize = self.r_long()
            retval.co_flags = self.r_long()
            retval.co_code = self.r_object()
            retval.co_consts = self.r_object()
            retval.co_names = self.r_object()
            retval.co_localsplusnames = self.r_object()
            retval.co_localspluskinds = self.r_object()
            retval.co_filename = self.r_object()
            retval.co_name = self.r_object()
            retval.co_qualname = self.r_object()
            retval.co_firstlineno = self.r_long()
            retval.co_linetable = self.r_object()
            retval.co_exceptiontable = self.r_object()
            return retval
        elif type == Type.REF:
            n = self.r_long()
            retval = self.refs[n]
            assert retval is not None
            return retval
        else:
            breakpoint()
            raise AssertionError(f"Unknown type {type} {chr(type)!r}")