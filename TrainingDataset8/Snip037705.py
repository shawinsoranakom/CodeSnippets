def _populate_app_pages(
    msg: Union[NewSession, PagesChanged], main_script_path: str
) -> None:
    for page_script_hash, page_info in source_util.get_pages(main_script_path).items():
        page_proto = msg.app_pages.add()

        page_proto.page_script_hash = page_script_hash
        page_proto.page_name = page_info["page_name"]
        page_proto.icon = page_info["icon"]