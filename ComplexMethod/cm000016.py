def emitter_converter(size_par, data):
    """
    :param size_par: how many parity bits the message must have
    :param data:  information bits
    :return: message to be transmitted by unreliable medium
            - bits of information merged with parity bits

    >>> emitter_converter(4, "101010111111")
    ['1', '1', '1', '1', '0', '1', '0', '0', '1', '0', '1', '1', '1', '1', '1', '1']
    >>> emitter_converter(5, "101010111111")
    Traceback (most recent call last):
        ...
    ValueError: size of parity don't match with size of data
    """
    if size_par + len(data) <= 2**size_par - (len(data) - 1):
        raise ValueError("size of parity don't match with size of data")

    data_out = []
    parity = []
    bin_pos = [bin(x)[2:] for x in range(1, size_par + len(data) + 1)]

    # sorted information data for the size of the output data
    data_ord = []
    # data position template + parity
    data_out_gab = []
    # parity bit counter
    qtd_bp = 0
    # counter position of data bits
    cont_data = 0

    for x in range(1, size_par + len(data) + 1):
        # Performs a template of bit positions - who should be given,
        # and who should be parity
        if qtd_bp < size_par:
            if (np.log(x) / np.log(2)).is_integer():
                data_out_gab.append("P")
                qtd_bp = qtd_bp + 1
            else:
                data_out_gab.append("D")
        else:
            data_out_gab.append("D")

        # Sorts the data to the new output size
        if data_out_gab[-1] == "D":
            data_ord.append(data[cont_data])
            cont_data += 1
        else:
            data_ord.append(None)

    # Calculates parity
    for bp in range(1, size_par + 1):
        # Bit counter one for a given parity
        cont_bo = 0
        # counter to control the loop reading
        for cont_loop, x in enumerate(data_ord):
            if x is not None:
                try:
                    aux = (bin_pos[cont_loop])[-1 * (bp)]
                except IndexError:
                    aux = "0"
                if aux == "1" and x == "1":
                    cont_bo += 1
        parity.append(cont_bo % 2)

    # Mount the message
    cont_bp = 0  # parity bit counter
    for x in range(size_par + len(data)):
        if data_ord[x] is None:
            data_out.append(str(parity[cont_bp]))
            cont_bp += 1
        else:
            data_out.append(data_ord[x])

    return data_out