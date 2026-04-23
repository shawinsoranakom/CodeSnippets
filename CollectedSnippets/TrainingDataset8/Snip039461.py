def _create_dataframe_msg(df, id=1):
    msg = ForwardMsg()
    msg.metadata.delta_path[:] = [RootContainer.SIDEBAR, id]
    data_frame.marshall_data_frame(df, msg.delta.new_element.data_frame)
    return msg