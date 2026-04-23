def _fix(node, lineno, col_offset, end_lineno, end_col_offset):
        if 'lineno' in node._attributes:
            if not hasattr(node, 'lineno'):
                node.lineno = lineno
            else:
                lineno = node.lineno
        if 'end_lineno' in node._attributes:
            if getattr(node, 'end_lineno', None) is None:
                node.end_lineno = end_lineno
            else:
                end_lineno = node.end_lineno
        if 'col_offset' in node._attributes:
            if not hasattr(node, 'col_offset'):
                node.col_offset = col_offset
            else:
                col_offset = node.col_offset
        if 'end_col_offset' in node._attributes:
            if getattr(node, 'end_col_offset', None) is None:
                node.end_col_offset = end_col_offset
            else:
                end_col_offset = node.end_col_offset
        for child in iter_child_nodes(node):
            _fix(child, lineno, col_offset, end_lineno, end_col_offset)