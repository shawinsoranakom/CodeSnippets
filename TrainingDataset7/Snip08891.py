def handle_extensions(extensions):
    """
    Organize multiple extensions that are separated with commas or passed by
    using --extension/-e multiple times.

    For example: running 'django-admin makemessages -e js,txt -e xhtml -a'
    would result in an extension list: ['.js', '.txt', '.xhtml']

    >>> handle_extensions(['.html', 'html,js,py,py,py,.py', 'py,.py'])
    {'.html', '.js', '.py'}
    >>> handle_extensions(['.html, txt,.tpl'])
    {'.html', '.tpl', '.txt'}
    """
    ext_list = []
    for ext in extensions:
        ext_list.extend(ext.replace(" ", "").split(","))
    for i, ext in enumerate(ext_list):
        if not ext.startswith("."):
            ext_list[i] = ".%s" % ext_list[i]
    return set(ext_list)