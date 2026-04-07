def __iter__(self):
        return ((i, f"Item #{i}") for i in range(1, 4))