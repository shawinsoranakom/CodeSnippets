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