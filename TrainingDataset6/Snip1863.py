def update_content(*, content_path: Path, new_content: Any) -> bool:
    old_content = content_path.read_text(encoding="utf-8")

    new_content = yaml.dump(new_content, sort_keys=False, width=200, allow_unicode=True)
    if old_content == new_content:
        logging.info(f"The content hasn't changed for {content_path}")
        return False
    content_path.write_text(new_content, encoding="utf-8")
    logging.info(f"Updated {content_path}")
    return True