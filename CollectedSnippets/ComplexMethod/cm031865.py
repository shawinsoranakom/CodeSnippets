def _inverse_lookup(packed, pos):
    result = bytearray()
    node_offset = 0
    while 1:
        node_count, final, edge_offset = decode_node(packed, node_offset)
        if final:
            if pos == 0:
                return bytes(result)
            pos -= 1
        prev_child_offset = edge_offset
        edgeindex = 0
        while 1:
            child_offset, last_edge, size, edgelabel_chars_offset = decode_edge(packed, edgeindex, prev_child_offset, edge_offset)
            edgeindex += 1
            prev_child_offset = child_offset
            descendant_count, _, _ = decode_node(packed, child_offset)
            nextpos = pos - descendant_count
            if nextpos < 0:
                assert edgelabel_chars_offset >= 0
                result.extend(packed[edgelabel_chars_offset: edgelabel_chars_offset + size])
                node_offset = child_offset
                break
            elif not last_edge:
                pos = nextpos
                edge_offset = edgelabel_chars_offset + size
            else:
                raise KeyError
        else:
            raise KeyError