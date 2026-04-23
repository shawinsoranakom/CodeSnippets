def handle_default_options(options):
    """
    Include any default options that all commands should accept here
    so that ManagementUtility can handle them before searching for
    user commands.
    """
    if options.settings:
        os.environ["DJANGO_SETTINGS_MODULE"] = options.settings
    if options.pythonpath:
        sys.path.insert(0, options.pythonpath)