def _decrypt_url(png):
        encrypted_data = io.BytesIO(compat_b64decode(png)[8:])
        while True:
            length = compat_struct_unpack('!I', encrypted_data.read(4))[0]
            chunk_type = encrypted_data.read(4)
            if chunk_type == b'IEND':
                break
            data = encrypted_data.read(length)
            if chunk_type == b'tEXt':
                alphabet_data, text = data.split(b'\0')
                quality, url_data = text.split(b'%%')
                alphabet = []
                e = 0
                d = 0
                for l in _bytes_to_chr(alphabet_data):
                    if d == 0:
                        alphabet.append(l)
                        d = e = (e + 1) % 4
                    else:
                        d -= 1
                url = ''
                f = 0
                e = 3
                b = 1
                for letter in _bytes_to_chr(url_data):
                    if f == 0:
                        l = int(letter) * 10
                        f = 1
                    else:
                        if e == 0:
                            l += int(letter)
                            url += alphabet[l]
                            e = (b + 3) % 4
                            f = 0
                            b += 1
                        else:
                            e -= 1

                yield quality.decode(), url
            encrypted_data.read(4)