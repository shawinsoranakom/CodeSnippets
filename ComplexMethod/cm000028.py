def __multiply(self):
        dft_a = self.__dft("A")
        dft_b = self.__dft("B")
        inverce_c = [[dft_a[i] * dft_b[i] for i in range(self.c_max_length)]]
        del dft_a
        del dft_b

        # Corner Case
        if len(inverce_c[0]) <= 1:
            return inverce_c[0]
        # Inverse DFT
        next_ncol = 2
        while next_ncol <= self.c_max_length:
            new_inverse_c = [[] for i in range(next_ncol)]
            root = self.root ** (next_ncol // 2)
            current_root = 1
            # First half of next step
            for j in range(self.c_max_length // next_ncol):
                for i in range(next_ncol // 2):
                    # Even positions
                    new_inverse_c[i].append(
                        (
                            inverce_c[i][j]
                            + inverce_c[i][j + self.c_max_length // next_ncol]
                        )
                        / 2
                    )
                    # Odd positions
                    new_inverse_c[i + next_ncol // 2].append(
                        (
                            inverce_c[i][j]
                            - inverce_c[i][j + self.c_max_length // next_ncol]
                        )
                        / (2 * current_root)
                    )
                current_root *= root
            # Update
            inverce_c = new_inverse_c
            next_ncol *= 2
        # Unpack
        inverce_c = [
            complex(round(x[0].real, 8), round(x[0].imag, 8)) for x in inverce_c
        ]

        # Remove leading 0's
        while inverce_c[-1] == 0:
            inverce_c.pop()
        return inverce_c