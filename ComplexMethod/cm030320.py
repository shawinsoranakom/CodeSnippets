def close(self):
        if self.closed:
            return
        try:
            super().close()
            # Flush any data from the compressor, and update header info
            if self._compressor:
                buf = self._compressor.flush()
                self._compress_size += len(buf)
                self._fileobj.write(buf)
                self._zinfo.compress_size = self._compress_size
            else:
                self._zinfo.compress_size = self._file_size
            self._zinfo.CRC = self._crc
            self._zinfo.file_size = self._file_size

            if not self._zip64:
                if self._file_size > ZIP64_LIMIT:
                    raise RuntimeError("File size too large, try using force_zip64")
                if self._compress_size > ZIP64_LIMIT:
                    raise RuntimeError("Compressed size too large, try using force_zip64")

            # Write updated header info
            if self._zinfo.flag_bits & _MASK_USE_DATA_DESCRIPTOR:
                # Write CRC and file sizes after the file data
                fmt = '<LLQQ' if self._zip64 else '<LLLL'
                self._fileobj.write(struct.pack(fmt, _DD_SIGNATURE, self._zinfo.CRC,
                    self._zinfo.compress_size, self._zinfo.file_size))
                self._zipfile.start_dir = self._fileobj.tell()
            else:
                # Seek backwards and write file header (which will now include
                # correct CRC and file sizes)

                # Preserve current position in file
                self._zipfile.start_dir = self._fileobj.tell()
                self._fileobj.seek(self._zinfo.header_offset)
                self._fileobj.write(self._zinfo.FileHeader(self._zip64))
                self._fileobj.seek(self._zipfile.start_dir)

            # Successfully written: Add file to our caches
            self._zipfile.filelist.append(self._zinfo)
            self._zipfile.NameToInfo[self._zinfo.filename] = self._zinfo
        finally:
            self._zipfile._writing = False