def generate_app(
    name: str | None,
    description: str | None,
    redirect_uris: str | None,
    scopes: str | None,
    grant_types: str | None,
):
    """Generate credentials for a new OAuth application

    All options are optional. If not provided, you will be prompted interactively.
    """
    # Interactive prompts for missing required values
    if name is None:
        name = prompt_for_name()

    if description is None:
        description = prompt_for_description()

    if redirect_uris is None:
        redirect_uris_list = prompt_for_redirect_uris()
    else:
        redirect_uris_list = [uri.strip() for uri in redirect_uris.split(",")]

    if scopes is None:
        scopes_list = prompt_for_scopes()
    else:
        scopes_list = [scope.strip() for scope in scopes.split(",")]

    if grant_types is None:
        grant_types_list = prompt_for_grant_types()
    else:
        grant_types_list = [gt.strip() for gt in grant_types.split(",")]

    try:
        creds = generate_app_credentials(
            name=name,
            description=description,
            redirect_uris=redirect_uris_list,
            scopes=scopes_list,
            grant_types=grant_types_list,
        )

        sql = format_sql_insert(creds)
        click.echo(sql)

    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)