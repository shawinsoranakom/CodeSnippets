def __init__(self, file_contents):
        self._patched_functions = {
            (TimerClass, 'addEventListener'): lambda params: undefined,
        }
        code_tag = next(tag
                        for tag_code, tag in _extract_tags(file_contents)
                        if tag_code == 82)
        p = code_tag.index(b'\0', 4) + 1
        code_reader = io.BytesIO(code_tag[p:])

        # Parse ABC (AVM2 ByteCode)

        # Define a couple convenience methods
        u30 = lambda *args: _u30(*args, reader=code_reader)
        s32 = lambda *args: _s32(*args, reader=code_reader)
        u32 = lambda *args: _u32(*args, reader=code_reader)
        read_bytes = lambda *args: _read_bytes(*args, reader=code_reader)
        read_byte = lambda *args: _read_byte(*args, reader=code_reader)

        # minor_version + major_version
        read_bytes(2 + 2)

        # Constant pool
        int_count = u30()
        self.constant_ints = [0]
        for _c in range(1, int_count):
            self.constant_ints.append(s32())
        self.constant_uints = [0]
        uint_count = u30()
        for _c in range(1, uint_count):
            self.constant_uints.append(u32())
        double_count = u30()
        read_bytes(max(0, (double_count - 1)) * 8)
        string_count = u30()
        self.constant_strings = ['']
        for _c in range(1, string_count):
            s = _read_string(code_reader)
            self.constant_strings.append(s)
        namespace_count = u30()
        for _c in range(1, namespace_count):
            read_bytes(1)  # kind
            u30()  # name
        ns_set_count = u30()
        for _c in range(1, ns_set_count):
            count = u30()
            for _c2 in range(count):
                u30()
        multiname_count = u30()
        MULTINAME_SIZES = {
            0x07: 2,  # QName
            0x0d: 2,  # QNameA
            0x0f: 1,  # RTQName
            0x10: 1,  # RTQNameA
            0x11: 0,  # RTQNameL
            0x12: 0,  # RTQNameLA
            0x09: 2,  # Multiname
            0x0e: 2,  # MultinameA
            0x1b: 1,  # MultinameL
            0x1c: 1,  # MultinameLA
        }
        self.multinames = ['']
        for _c in range(1, multiname_count):
            kind = u30()
            assert kind in MULTINAME_SIZES, 'Invalid multiname kind %r' % kind
            if kind == 0x07:
                u30()  # namespace_idx
                name_idx = u30()
                self.multinames.append(self.constant_strings[name_idx])
            elif kind == 0x09:
                name_idx = u30()
                u30()
                self.multinames.append(self.constant_strings[name_idx])
            else:
                self.multinames.append(_Multiname(kind))
                for _c2 in range(MULTINAME_SIZES[kind]):
                    u30()

        # Methods
        method_count = u30()
        MethodInfo = collections.namedtuple(
            'MethodInfo',
            ['NEED_ARGUMENTS', 'NEED_REST'])
        method_infos = []
        for method_id in range(method_count):
            param_count = u30()
            u30()  # return type
            for _ in range(param_count):
                u30()  # param type
            u30()  # name index (always 0 for youtube)
            flags = read_byte()
            if flags & 0x08 != 0:
                # Options present
                option_count = u30()
                for c in range(option_count):
                    u30()  # val
                    read_bytes(1)  # kind
            if flags & 0x80 != 0:
                # Param names present
                for _ in range(param_count):
                    u30()  # param name
            mi = MethodInfo(flags & 0x01 != 0, flags & 0x04 != 0)
            method_infos.append(mi)

        # Metadata
        metadata_count = u30()
        for _c in range(metadata_count):
            u30()  # name
            item_count = u30()
            for _c2 in range(item_count):
                u30()  # key
                u30()  # value

        def parse_traits_info():
            trait_name_idx = u30()
            kind_full = read_byte()
            kind = kind_full & 0x0f
            attrs = kind_full >> 4
            methods = {}
            constants = None
            if kind == 0x00:  # Slot
                u30()  # Slot id
                u30()  # type_name_idx
                vindex = u30()
                if vindex != 0:
                    read_byte()  # vkind
            elif kind == 0x06:  # Const
                u30()  # Slot id
                u30()  # type_name_idx
                vindex = u30()
                vkind = 'any'
                if vindex != 0:
                    vkind = read_byte()
                if vkind == 0x03:  # Constant_Int
                    value = self.constant_ints[vindex]
                elif vkind == 0x04:  # Constant_UInt
                    value = self.constant_uints[vindex]
                else:
                    return {}, None  # Ignore silently for now
                constants = {self.multinames[trait_name_idx]: value}
            elif kind in (0x01, 0x02, 0x03):  # Method / Getter / Setter
                u30()  # disp_id
                method_idx = u30()
                methods[self.multinames[trait_name_idx]] = method_idx
            elif kind == 0x04:  # Class
                u30()  # slot_id
                u30()  # classi
            elif kind == 0x05:  # Function
                u30()  # slot_id
                function_idx = u30()
                methods[function_idx] = self.multinames[trait_name_idx]
            else:
                raise ExtractorError('Unsupported trait kind %d' % kind)

            if attrs & 0x4 != 0:  # Metadata present
                metadata_count = u30()
                for _c3 in range(metadata_count):
                    u30()  # metadata index

            return methods, constants

        # Classes
        class_count = u30()
        classes = []
        for class_id in range(class_count):
            name_idx = u30()

            cname = self.multinames[name_idx]
            avm_class = _AVMClass(name_idx, cname)
            classes.append(avm_class)

            u30()  # super_name idx
            flags = read_byte()
            if flags & 0x08 != 0:  # Protected namespace is present
                u30()  # protected_ns_idx
            intrf_count = u30()
            for _c2 in range(intrf_count):
                u30()
            u30()  # iinit
            trait_count = u30()
            for _c2 in range(trait_count):
                trait_methods, trait_constants = parse_traits_info()
                avm_class.register_methods(trait_methods)
                if trait_constants:
                    avm_class.constants.update(trait_constants)

        assert len(classes) == class_count
        self._classes_by_name = dict((c.name, c) for c in classes)

        for avm_class in classes:
            avm_class.cinit_idx = u30()
            trait_count = u30()
            for _c2 in range(trait_count):
                trait_methods, trait_constants = parse_traits_info()
                avm_class.register_methods(trait_methods)
                if trait_constants:
                    avm_class.constants.update(trait_constants)

        # Scripts
        script_count = u30()
        for _c in range(script_count):
            u30()  # init
            trait_count = u30()
            for _c2 in range(trait_count):
                parse_traits_info()

        # Method bodies
        method_body_count = u30()
        Method = collections.namedtuple('Method', ['code', 'local_count'])
        self._all_methods = []
        for _c in range(method_body_count):
            method_idx = u30()
            u30()  # max_stack
            local_count = u30()
            u30()  # init_scope_depth
            u30()  # max_scope_depth
            code_length = u30()
            code = read_bytes(code_length)
            m = Method(code, local_count)
            self._all_methods.append(m)
            for avm_class in classes:
                if method_idx in avm_class.method_idxs:
                    avm_class.methods[avm_class.method_idxs[method_idx]] = m
            exception_count = u30()
            for _c2 in range(exception_count):
                u30()  # from
                u30()  # to
                u30()  # target
                u30()  # exc_type
                u30()  # var_name
            trait_count = u30()
            for _c2 in range(trait_count):
                parse_traits_info()

        assert p + code_reader.tell() == len(code_tag)