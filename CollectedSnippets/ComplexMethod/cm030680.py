def test_read_readinto_readinto1(self):
        lst = []
        with ZstdFile(io.BytesIO(COMPRESSED_THIS_FILE*5)) as f:
            while True:
                method = random.randint(0, 2)
                size = random.randint(0, 300)

                if method == 0:
                    dat = f.read(size)
                    if not dat and size:
                        break
                    lst.append(dat)
                elif method == 1:
                    ba = bytearray(size)
                    read_size = f.readinto(ba)
                    if read_size == 0 and size:
                        break
                    lst.append(bytes(ba[:read_size]))
                elif method == 2:
                    ba = bytearray(size)
                    read_size = f.readinto1(ba)
                    if read_size == 0 and size:
                        break
                    lst.append(bytes(ba[:read_size]))
        self.assertEqual(b''.join(lst), THIS_FILE_BYTES*5)