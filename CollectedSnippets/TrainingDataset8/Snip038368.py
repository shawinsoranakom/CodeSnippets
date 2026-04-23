def _print_url(is_running_hello: bool) -> None:
    if is_running_hello:
        title_message = "Welcome to Streamlit. Check out our demo in your browser."
    else:
        title_message = "You can now view your Streamlit app in your browser."

    named_urls = []

    if config.is_manually_set("browser.serverAddress"):
        named_urls = [
            ("URL", server_util.get_url(config.get_option("browser.serverAddress")))
        ]

    elif (
        config.is_manually_set("server.address") and not server_address_is_unix_socket()
    ):
        named_urls = [
            ("URL", server_util.get_url(config.get_option("server.address"))),
        ]

    elif server_address_is_unix_socket():
        named_urls = [
            ("Unix Socket", config.get_option("server.address")),
        ]

    elif config.get_option("server.headless"):
        internal_ip = net_util.get_internal_ip()
        if internal_ip:
            named_urls.append(("Network URL", server_util.get_url(internal_ip)))

        external_ip = net_util.get_external_ip()
        if external_ip:
            named_urls.append(("External URL", server_util.get_url(external_ip)))

    else:
        named_urls = [
            ("Local URL", server_util.get_url("localhost")),
        ]

        internal_ip = net_util.get_internal_ip()
        if internal_ip:
            named_urls.append(("Network URL", server_util.get_url(internal_ip)))

    click.secho("")
    click.secho("  %s" % title_message, fg="blue", bold=True)
    click.secho("")

    for url_name, url in named_urls:
        url_util.print_url(url_name, url)

    click.secho("")

    if is_running_hello:
        click.secho("  Ready to create your own Python apps super quickly?")
        click.secho("  Head over to ", nl=False)
        click.secho("https://docs.streamlit.io", bold=True)
        click.secho("")
        click.secho("  May you create awesome apps!")
        click.secho("")
        click.secho("")