def compare_ordering_key(k):
                if k[1] is None:
                    return (1, 0)  # +infinity, larger than any number
                return (0, k[1])