class PolybiusCipher:
    def __init__(self) -> None:
        self.SQUARE = np.array(SQUARE)

    def letter_to_numbers(self, letter: str) -> np.ndarray:
        index1, index2 = np.where(letter == self.SQUARE)
        indexes = np.concatenate([index1 + 1, index2 + 1])
        return indexes

    def numbers_to_letter(self, index1: int, index2: int) -> str:
        return self.SQUARE[index1 - 1, index2 - 1]

    def encode(self, message: str) -> str:
        message = message.lower()
        message = message.replace("j", "i")

        encoded_message = ""
        for letter_index in range(len(message)):
            if message[letter_index] != " ":
                numbers = self.letter_to_numbers(message[letter_index])
                encoded_message = encoded_message + str(numbers[0]) + str(numbers[1])
            elif message[letter_index] == " ":
                encoded_message = encoded_message + " "

        return encoded_message

    def decode(self, message: str) -> str:
        message = message.replace(" ", "  ")
        decoded_message = ""
        for numbers_index in range(int(len(message) / 2)):
            if message[numbers_index * 2] != " ":
                index1 = message[numbers_index * 2]
                index2 = message[numbers_index * 2 + 1]

                letter = self.numbers_to_letter(int(index1), int(index2))
                decoded_message = decoded_message + letter
            elif message[numbers_index * 2] == " ":
                decoded_message = decoded_message + " "

        return decoded_message
