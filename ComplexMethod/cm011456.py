def _create_table(
    shards: list[tuple[tuple[int, int], tuple[int, int], int]], device_kind: str = ""
):
    """
    Creates a tabulate table given row and column ranges with device name
    """
    from tabulate import tabulate

    # Extract unique row and column ranges
    row_ranges = sorted({block[0] for block in shards})
    col_ranges = sorted({block[1] for block in shards})

    # Create a matrix initialized with empty strings
    matrix = [["" for _ in col_ranges] for _ in row_ranges]

    # Fill the matrix with values
    for block in shards:
        row_index = row_ranges.index(block[0])
        col_index = col_ranges.index(block[1])
        if matrix[row_index][col_index] == "":
            matrix[row_index][col_index] = device_kind + ":" + str(block[2])
        else:
            matrix[row_index][col_index] += "," + str(block[2])

    # Prepare headers
    row_headers = [f"Row {r[0]}-{r[1]}" for r in row_ranges]
    col_headers = [f"Col {c[0]}-{c[1]}" for c in col_ranges]

    return tabulate(matrix, headers=col_headers, showindex=row_headers)