def save_picklebuffer(self, obj):
            if self.proto < 5:
                raise PicklingError("PickleBuffer can only be pickled with "
                                    "protocol >= 5")
            with obj.raw() as m:
                if not m.contiguous:
                    raise PicklingError("PickleBuffer can not be pickled when "
                                        "pointing to a non-contiguous buffer")
                in_band = True
                if self._buffer_callback is not None:
                    in_band = bool(self._buffer_callback(obj))
                if in_band:
                    # Write data in-band
                    # XXX The C implementation avoids a copy here
                    buf = m.tobytes()
                    in_memo = id(buf) in self.memo
                    if m.readonly:
                        if in_memo:
                            self._save_bytes_no_memo(buf)
                        else:
                            self.save_bytes(buf)
                    else:
                        if in_memo:
                            self._save_bytearray_no_memo(buf)
                        else:
                            self.save_bytearray(buf)
                else:
                    # Write data out-of-band
                    self.write(NEXT_BUFFER)
                    if m.readonly:
                        self.write(READONLY_BUFFER)