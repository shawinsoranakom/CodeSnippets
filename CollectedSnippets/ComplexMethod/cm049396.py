def get_certificate_end_date():
    """Check if the certificate is up to date and valid

    :return: End date of the certificate if it is valid, None otherwise
    :rtype: str
    """
    base_path = [get_path_nginx(), 'conf'] if IS_WINDOWS else ['/etc/ssl/certs']
    path = Path(*base_path, 'nginx-cert.crt')
    if not path.exists():
        return None

    try:
        cert = x509.load_pem_x509_certificate(path.read_bytes())
    except ValueError:
        _logger.exception("Unable to read certificate file.")
        return None

    common_name = next(
        (name_attribute.value for name_attribute in cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)), ''
    )

    # Ensure cryptography compatibility with python < 3.13
    if IS_RPI and float(get_version()[1:8]) < 2025.10:
        cert_end_date = cert.not_valid_after
    else:
        cert_end_date = cert.not_valid_after_utc.replace(tzinfo=None)

    if (
        common_name == 'OdooTempIoTBoxCertificate'
        or datetime.datetime.now() > cert_end_date - datetime.timedelta(days=10)
    ):
        _logger.debug("SSL certificate '%s' must be updated.", common_name)
        return None

    _logger.debug("SSL certificate '%s' is valid until %s", common_name, cert_end_date)
    return str(cert_end_date)