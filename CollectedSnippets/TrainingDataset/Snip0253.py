def main() -> None:
    n = int(input("Enter the order of the encryption key: "))
    hill_matrix = []

    print("Enter each row of the encryption key with space separated integers")
    for _ in range(n):
        row = [int(x) for x in input().split()]
        hill_matrix.append(row)

    hc = HillCipher(np.array(hill_matrix))

    print("Would you like to encrypt or decrypt some text? (1 or 2)")
    option = input("\n1. Encrypt\n2. Decrypt\n")
    if option == "1":
        text_e = input("What text would you like to encrypt?: ")
        print("Your encrypted text is:")
        print(hc.encrypt(text_e))
    elif option == "2":
        text_d = input("What text would you like to decrypt?: ")
        print("Your decrypted text is:")
        print(hc.decrypt(text_d))
