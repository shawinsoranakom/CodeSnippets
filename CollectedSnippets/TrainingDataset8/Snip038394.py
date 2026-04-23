def activate(ctx):
    """Activate Streamlit by entering your email."""
    if not ctx.invoked_subcommand:
        Credentials.get_current().activate()