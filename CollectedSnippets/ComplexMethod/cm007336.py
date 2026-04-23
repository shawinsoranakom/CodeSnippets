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