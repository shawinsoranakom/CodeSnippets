def create_dataframe_msg(df: Data, id: int = 1) -> ForwardMsg:
    """Create a mock legacy_data_frame ForwardMsg."""
    msg = ForwardMsg()
    msg.metadata.delta_path[:] = make_delta_path(RootContainer.SIDEBAR, (), id)
    legacy_data_frame.marshall_data_frame(df, msg.delta.new_element.data_frame)
    return msg