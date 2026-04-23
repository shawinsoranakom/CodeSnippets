def receptor_converter(size_par, data):
    """
    >>> receptor_converter(4, "1111010010111111")
    (['1', '0', '1', '0', '1', '0', '1', '1', '1', '1', '1', '1'], True)
    """
    # data position template + parity
    data_out_gab = []
    # Parity bit counter
    qtd_bp = 0
    # Counter p data bit reading
    cont_data = 0
    # list of parity received
    parity_received = []
    data_output = []

    for i, item in enumerate(data, 1):
        # Performs a template of bit positions - who should be given,
        #  and who should be parity
        if qtd_bp < size_par and (np.log(i) / np.log(2)).is_integer():
            data_out_gab.append("P")
            qtd_bp = qtd_bp + 1
        else:
            data_out_gab.append("D")

        # Sorts the data to the new output size
        if data_out_gab[-1] == "D":
            data_output.append(item)
        else:
            parity_received.append(item)

    # -----------calculates the parity with the data
    data_out = []
    parity = []
    bin_pos = [bin(x)[2:] for x in range(1, size_par + len(data_output) + 1)]

    #  sorted information data for the size of the output data
    data_ord = []
    # Data position feedback + parity
    data_out_gab = []
    # Parity bit counter
    qtd_bp = 0
    # Counter p data bit reading
    cont_data = 0

    for x in range(1, size_par + len(data_output) + 1):
        # Performs a template position of bits - who should be given,
        # and who should be parity
        if qtd_bp < size_par and (np.log(x) / np.log(2)).is_integer():
            data_out_gab.append("P")
            qtd_bp = qtd_bp + 1
        else:
            data_out_gab.append("D")

        # Sorts the data to the new output size
        if data_out_gab[-1] == "D":
            data_ord.append(data_output[cont_data])
            cont_data += 1
        else:
            data_ord.append(None)

    # Calculates parity
    for bp in range(1, size_par + 1):
        # Bit counter one for a certain parity
        cont_bo = 0
        for cont_loop, x in enumerate(data_ord):
            if x is not None:
                try:
                    aux = (bin_pos[cont_loop])[-1 * (bp)]
                except IndexError:
                    aux = "0"
                if aux == "1" and x == "1":
                    cont_bo += 1
        parity.append(str(cont_bo % 2))

    # Mount the message
    cont_bp = 0  # Parity bit counter
    for x in range(size_par + len(data_output)):
        if data_ord[x] is None:
            data_out.append(str(parity[cont_bp]))
            cont_bp += 1
        else:
            data_out.append(data_ord[x])

    ack = parity_received == parity
    return data_output, ack