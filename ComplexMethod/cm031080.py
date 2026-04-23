def make_zip64_file(
        self, file_size_64_set=False, file_size_extra=False,
        compress_size_64_set=False, compress_size_extra=False,
        header_offset_64_set=False, header_offset_extra=False,
        extensible_data=b'',
        end_of_central_dir_size=None, offset_to_end_of_central_dir=None,
    ):
        """Generate bytes sequence for a zip with (incomplete) zip64 data.

        The actual values (not the zip 64 0xffffffff values) stored in the file
        are:
        file_size: 8
        compress_size: 8
        header_offset: 0
        """
        actual_size = 8
        actual_header_offset = 0
        local_zip64_fields = []
        central_zip64_fields = []

        file_size = actual_size
        if file_size_64_set:
            file_size = 0xffffffff
            if file_size_extra:
                local_zip64_fields.append(actual_size)
                central_zip64_fields.append(actual_size)
        file_size = struct.pack("<L", file_size)

        compress_size = actual_size
        if compress_size_64_set:
            compress_size = 0xffffffff
            if compress_size_extra:
                local_zip64_fields.append(actual_size)
                central_zip64_fields.append(actual_size)
        compress_size = struct.pack("<L", compress_size)

        header_offset = actual_header_offset
        if header_offset_64_set:
            header_offset = 0xffffffff
            if header_offset_extra:
                central_zip64_fields.append(actual_header_offset)
        header_offset = struct.pack("<L", header_offset)

        local_extra = struct.pack(
            '<HH' + 'Q'*len(local_zip64_fields),
            0x0001,
            8*len(local_zip64_fields),
            *local_zip64_fields
        )

        central_extra = struct.pack(
            '<HH' + 'Q'*len(central_zip64_fields),
            0x0001,
            8*len(central_zip64_fields),
            *central_zip64_fields
        )

        central_dir_size = struct.pack('<Q', 58 + 8 * len(central_zip64_fields))
        offset_to_central_dir = struct.pack('<Q', 50 + 8 * len(local_zip64_fields))
        if end_of_central_dir_size is None:
            end_of_central_dir_size = 44 + len(extensible_data)
        if offset_to_end_of_central_dir is None:
            offset_to_end_of_central_dir = (108
                                            + 8 * len(local_zip64_fields)
                                            + 8 * len(central_zip64_fields))

        local_extra_length = struct.pack("<H", 4 + 8 * len(local_zip64_fields))
        central_extra_length = struct.pack("<H", 4 + 8 * len(central_zip64_fields))

        filename = b"test.txt"
        content = b"test1234"
        filename_length = struct.pack("<H", len(filename))
        zip64_contents = (
            # Local file header
            b"PK\x03\x04\x14\x00\x00\x00\x00\x00\x00\x00!\x00\x9e%\xf5\xaf"
            + compress_size
            + file_size
            + filename_length
            + local_extra_length
            + filename
            + local_extra
            + content
            # Central directory:
            + b"PK\x01\x02-\x03-\x00\x00\x00\x00\x00\x00\x00!\x00\x9e%\xf5\xaf"
            + compress_size
            + file_size
            + filename_length
            + central_extra_length
            + b"\x00\x00\x00\x00\x00\x00\x00\x00\x80\x01"
            + header_offset
            + filename
            + central_extra
            # Zip64 end of central directory
            + b"PK\x06\x06"
            + struct.pack('<Q', end_of_central_dir_size)
            + b"-\x00-\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00"
            + b"\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00"
            + central_dir_size
            + offset_to_central_dir
            + extensible_data
            # Zip64 end of central directory locator
            + b"PK\x06\x07\x00\x00\x00\x00"
            + struct.pack('<Q', offset_to_end_of_central_dir)
            + b"\x01\x00\x00\x00"
            # end of central directory
            + b"PK\x05\x06\x00\x00\x00\x00\x01\x00\x01\x00:\x00\x00\x002\x00"
            + b"\x00\x00\x00\x00"
        )
        return zip64_contents