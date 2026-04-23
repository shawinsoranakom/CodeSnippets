def check_if_link_is_working(link: str) -> Tuple[bool, str]:
    """Checks if a link is working.

    If an error is identified when the request for the link occurs,
    the return will be a tuple with the first value True and the second
    value a string containing the error message.

    If no errors are identified, the return will be a tuple with the
    first value False and the second an empty string.
    """

    has_error = False
    error_message = ''

    try:
        resp = requests.get(link, timeout=25, headers={
            'User-Agent': fake_user_agent(),
            'host': get_host_from_link(link)
        })

        code = resp.status_code

        if code >= 400 and not has_cloudflare_protection(resp):
            has_error = True
            error_message = f'ERR:CLT: {code} : {link}'

    except requests.exceptions.SSLError as error:
        has_error = True
        error_message = f'ERR:SSL: {error} : {link}'

    except requests.exceptions.ConnectionError as error:
        has_error = True
        error_message = f'ERR:CNT: {error} : {link}'

    except (TimeoutError, requests.exceptions.ConnectTimeout):
        has_error = True
        error_message = f'ERR:TMO: {link}'

    except requests.exceptions.TooManyRedirects as error:
        has_error = True
        error_message = f'ERR:TMR: {error} : {link}'

    except (Exception, requests.exceptions.RequestException) as error:
        has_error = True
        error_message = f'ERR:UKN: {error} : {link}'

    return (has_error, error_message)