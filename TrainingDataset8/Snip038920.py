def get_cell_style(proto_df: DataFrame, col: int, row: int) -> CellStyle:
    """Returns the CellStyle for the given cell, or an empty CellStyle
    if no style for the given cell exists
    """
    if col >= len(proto_df.style.cols):
        return CellStyle()

    col_style = proto_df.style.cols[col]
    if row >= len(col_style.styles):
        return CellStyle()

    return col_style.styles[row]