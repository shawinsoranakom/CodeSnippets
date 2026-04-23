def _get_custom_display_values(translated_style: Dict[Any, Any]) -> Dict[Any, Any]:
    """Parses pandas.Styler style dictionary into a
    {(row, col): display_value} dictionary for cells whose display format
    has been customized.
    """
    # Create {(row, col): display_value} from translated_style['body']
    # translated_style['body'] has the shape:
    # [
    #   [ // row
    #     {  // cell or header
    #       'id': 'level0_row0' (for row header) | 'row0_col0' (for cells)
    #       'value': 1.329212
    #       'display_value': '132.92%'
    #       ...
    #     }
    #   ]
    # ]

    def has_custom_display_value(cell: Dict[Any, Any]) -> bool:
        # We'd prefer to only pass `display_value` data to the frontend
        # when a DataFrame cell has been custom-formatted by the user, to
        # save on bandwidth. However:
        #
        # Panda's Styler's internals are private, and it doesn't give us a
        # consistent way of testing whether a cell has a custom display_value
        # or not. Prior to Pandas 1.4, we could test whether a cell's
        # `display_value` differed from its `value`, and only stick the
        # `display_value` in the protobuf when that was the case. In 1.4, an
        # unmodified Styler will contain `display_value` strings for all
        # cells, regardless of whether any formatting has been applied to
        # that cell, so we no longer have this ability.
        #
        # So we're only testing that a cell's `display_value` is not None.
        # In Pandas 1.4, it seems that `display_value` is never None, so this
        # is purely a defense against future Styler changes.
        return cell.get("display_value") is not None

    cell_selector_regex = re.compile(r"row(\d+)_col(\d+)")
    header_selector_regex = re.compile(r"level(\d+)_row(\d+)")

    display_values = {}
    for row in translated_style["body"]:
        # row is a List[Dict], containing format data for each cell in the row,
        # plus an extra first entry for the row header, which we skip
        found_row_header = False
        for cell in row:
            cell_id = cell["id"]  # a string in the form 'row0_col0'
            if header_selector_regex.match(cell_id):
                if not found_row_header:
                    # We don't care about processing row headers, but as
                    # a sanity check, ensure we only see one per row
                    found_row_header = True
                    continue
                else:
                    raise RuntimeError('Found unexpected row header "%s"' % cell)
            match = cell_selector_regex.match(cell_id)
            if not match:
                raise RuntimeError('Failed to parse cell selector "%s"' % cell_id)

            if has_custom_display_value(cell):
                row = int(match.group(1))
                col = int(match.group(2))
                display_values[(row, col)] = str(cell["display_value"])

    return display_values