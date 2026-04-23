def __init__(self, sequence=None, *, name=None):
        if name is None or sequence is not None:
            sequence = sequence or ()
            _formats = [
                self._types_mapping[type(item)]
                    if not isinstance(item, (str, bytes))
                    else self._types_mapping[type(item)] % (
                        self._alignment * (len(item) // self._alignment + 1),
                    )
                for item in sequence
            ]
            self._list_len = len(_formats)
            assert sum(len(fmt) <= 8 for fmt in _formats) == self._list_len
            offset = 0
            # The offsets of each list element into the shared memory's
            # data area (0 meaning the start of the data area, not the start
            # of the shared memory area).
            self._allocated_offsets = [0]
            for fmt in _formats:
                offset += self._alignment if fmt[-1] != "s" else int(fmt[:-1])
                self._allocated_offsets.append(offset)
            _recreation_codes = [
                self._extract_recreation_code(item) for item in sequence
            ]
            requested_size = struct.calcsize(
                "q" + self._format_size_metainfo +
                "".join(_formats) +
                self._format_packing_metainfo +
                self._format_back_transform_codes
            )

            self.shm = SharedMemory(name, create=True, size=requested_size)
        else:
            self.shm = SharedMemory(name)

        if sequence is not None:
            _enc = _encoding
            struct.pack_into(
                "q" + self._format_size_metainfo,
                self.shm.buf,
                0,
                self._list_len,
                *(self._allocated_offsets)
            )
            struct.pack_into(
                "".join(_formats),
                self.shm.buf,
                self._offset_data_start,
                *(v.encode(_enc) if isinstance(v, str) else v for v in sequence)
            )
            struct.pack_into(
                self._format_packing_metainfo,
                self.shm.buf,
                self._offset_packing_formats,
                *(v.encode(_enc) for v in _formats)
            )
            struct.pack_into(
                self._format_back_transform_codes,
                self.shm.buf,
                self._offset_back_transform_codes,
                *(_recreation_codes)
            )

        else:
            self._list_len = len(self)  # Obtains size from offset 0 in buffer.
            self._allocated_offsets = list(
                struct.unpack_from(
                    self._format_size_metainfo,
                    self.shm.buf,
                    1 * 8
                )
            )