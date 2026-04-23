class ShuffledShiftCipher:

    def __init__(self, passcode: str | None = None) -> None:

        self.__passcode = passcode or self.__passcode_creator()
        self.__key_list = self.__make_key_list()
        self.__shift_key = self.__make_shift_key()

    def __str__(self) -> str:

        return "".join(self.__passcode)

    def __neg_pos(self, iterlist: list[int]) -> list[int]:

        for i in range(1, len(iterlist), 2):
            iterlist[i] *= -1
        return iterlist

    def __passcode_creator(self) -> list[str]:

        choices = string.ascii_letters + string.digits
        password = [random.choice(choices) for _ in range(random.randint(10, 20))]
        return password

    def __make_key_list(self) -> list[str]:

        key_list_options = (
            string.ascii_letters + string.digits + string.punctuation + " \t\n"
        )

        keys_l = []

        breakpoints = sorted(set(self.__passcode))
        temp_list: list[str] = []

        for i in key_list_options:
            temp_list.extend(i)


            if i in breakpoints or i == key_list_options[-1]:
                keys_l.extend(temp_list[::-1])
                temp_list.clear()

        return keys_l

    def __make_shift_key(self) -> int:

        num = sum(self.__neg_pos([ord(x) for x in self.__passcode]))
        return num if num > 0 else len(self.__passcode)

    def decrypt(self, encoded_message: str) -> str:

        decoded_message = ""

        for i in encoded_message:
            position = self.__key_list.index(i)
            decoded_message += self.__key_list[
                (position - self.__shift_key) % -len(self.__key_list)
            ]

        return decoded_message

    def encrypt(self, plaintext: str) -> str:

        encoded_message = ""

        for i in plaintext:
            position = self.__key_list.index(i)
            encoded_message += self.__key_list[
                (position + self.__shift_key) % len(self.__key_list)
            ]

        return encoded_message
