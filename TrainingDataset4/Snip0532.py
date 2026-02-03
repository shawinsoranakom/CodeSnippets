def __repr__(self) -> str:
    values_list = []
    aux = self._front
    while aux is not None:
        values_list.append(aux.val)
        aux = aux.next_node

    return f"[{', '.join(repr(val) for val in values_list)}]"
