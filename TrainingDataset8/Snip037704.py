def _populate_user_info_msg(msg: UserInfo) -> None:
    msg.installation_id = Installation.instance().installation_id
    msg.installation_id_v3 = Installation.instance().installation_id_v3
    if Credentials.get_current().activation:
        msg.email = Credentials.get_current().activation.email
    else:
        msg.email = ""