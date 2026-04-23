class HillCipher:
    key_string = string.ascii_uppercase + string.digits

    modulus = np.vectorize(lambda x: x % 36)

    to_int = np.vectorize(round)

    def __init__(self, encrypt_key: np.ndarray) -> None:
        """
        encrypt_key is an NxN numpy array
        """
        self.encrypt_key = self.modulus(encrypt_key)  
        self.check_determinant()  
        self.break_key = encrypt_key.shape[0]

    def replace_letters(self, letter: str) -> int:
        
        return self.key_string.index(letter)

    def replace_digits(self, num: int) -> str:
       
        return self.key_string[int(num)]

    def check_determinant(self) -> None:
        
        det = round(np.linalg.det(self.encrypt_key))

        if det < 0:
            det = det % len(self.key_string)

        req_l = len(self.key_string)
        if greatest_common_divisor(det, len(self.key_string)) != 1:
            msg = (
                f"determinant modular {req_l} of encryption key({det}) "
                f"is not co prime w.r.t {req_l}.\nTry another key."
            )
            raise ValueError(msg)

    def process_text(self, text: str) -> str:
        
        chars = [char for char in text.upper() if char in self.key_string]

        last = chars[-1]
        while len(chars) % self.break_key != 0:
            chars.append(last)

        return "".join(chars)

    def encrypt(self, text: str) -> str:
       
        text = self.process_text(text.upper())
        encrypted = ""

        for i in range(0, len(text) - self.break_key + 1, self.break_key):
            batch = text[i : i + self.break_key]
            vec = [self.replace_letters(char) for char in batch]
            batch_vec = np.array([vec]).T
            batch_encrypted = self.modulus(self.encrypt_key.dot(batch_vec)).T.tolist()[
                0
            ]
            encrypted_batch = "".join(
                self.replace_digits(num) for num in batch_encrypted
            )
            encrypted += encrypted_batch

        return encrypted

    def make_decrypt_key(self) -> np.ndarray:
       
        det = round(np.linalg.det(self.encrypt_key))

        if det < 0:
            det = det % len(self.key_string)
        det_inv = None
        for i in range(len(self.key_string)):
            if (det * i) % len(self.key_string) == 1:
                det_inv = i
                break

        inv_key = (
            det_inv * np.linalg.det(self.encrypt_key) * np.linalg.inv(self.encrypt_key)
        )

        return self.to_int(self.modulus(inv_key))

    def decrypt(self, text: str) -> str:
        
        decrypt_key = self.make_decrypt_key()
        text = self.process_text(text.upper())
        decrypted = ""

        for i in range(0, len(text) - self.break_key + 1, self.break_key):
            batch = text[i : i + self.break_key]
            vec = [self.replace_letters(char) for char in batch]
            batch_vec = np.array([vec]).T
            batch_decrypted = self.modulus(decrypt_key.dot(batch_vec)).T.tolist()[0]
            decrypted_batch = "".join(
                self.replace_digits(num) for num in batch_decrypted
            )
            decrypted += decrypted_batch

        return decrypted
