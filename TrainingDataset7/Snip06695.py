def chunk(data, index):
    """
    Split a string into two parts at the input index.
    """
    return data[:index], data[index:]