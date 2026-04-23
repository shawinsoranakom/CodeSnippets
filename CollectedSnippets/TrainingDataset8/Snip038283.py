def print_url(title, url):
    """Pretty-print a URL on the terminal."""
    import click

    click.secho("  %s: " % title, nl=False, fg="blue")
    click.secho(url, bold=True)