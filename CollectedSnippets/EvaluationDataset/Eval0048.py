class XORCipher:
    def __init__(self, key: int = 0):
        """
        simple constructor that receives a key or uses
        default key = 0
        """

        self.__key = key

    def encrypt(self, content: str, key: int) -> list[str]:
       
        assert isinstance(key, int)
        assert isinstance(content, str)

        key = key or self.__key or 1

        key %= 256

        return [chr(ord(ch) ^ key) for ch in content]

    def decrypt(self, content: str, key: int) -> list[str]:
       
        assert isinstance(key, int)
        assert isinstance(content, str)

        key = key or self.__key or 1

        key %= 256

        return [chr(ord(ch) ^ key) for ch in content]

    def encrypt_string(self, content: str, key: int = 0) -> str:
       
        assert isinstance(key, int)
        assert isinstance(content, str)

        key = key or self.__key or 1

        key %= 256

        ans = ""

        for ch in content:
            ans += chr(ord(ch) ^ key)

        return ans

    def decrypt_string(self, content: str, key: int = 0) -> str:
       
        assert isinstance(key, int)
        assert isinstance(content, str)

        key = key or self.__key or 1

        key %= 256

        ans = ""

        for ch in content:
            ans += chr(ord(ch) ^ key)

        return ans

    def encrypt_file(self, file: str, key: int = 0) -> bool:

        assert isinstance(file, str)
        assert isinstance(key, int)

        key %= 256

        try:
            with open(file) as fin, open("encrypt.out", "w+") as fout:
                for line in fin:
                    fout.write(self.encrypt_string(line, key))

        except OSError:
            return False

        return True

    def decrypt_file(self, file: str, key: int) -> bool:
        """
        input: filename (str) and a key (int)
        output: returns true if decrypt process was
        successful otherwise false
        if key not passed the method uses the key by the constructor.
        otherwise key = 1
        """

        assert isinstance(file, str)
        assert isinstance(key, int)

        key %= 256

        try:
            with open(file) as fin, open("decrypt.out", "w+") as fout:
                for line in fin:
                    fout.write(self.decrypt_string(line, key))

        except OSError:
            return False

        return True
