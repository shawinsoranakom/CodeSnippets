def watch_for_template_changes(sender, **kwargs):
    for directory in get_template_directories():
        sender.watch_dir(directory, "**/*")