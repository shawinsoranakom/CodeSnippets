def download_odoo_certificate(retry=0):
    """Send a request to Odoo with customer db_uuid and enterprise_code
    to get a true certificate
    """
    if IS_TEST:
        _logger.info("Skipping certificate download in test mode.")
        return None
    db_uuid = get_conf('db_uuid')
    enterprise_code = get_conf('enterprise_code')
    if not db_uuid:
        return None
    try:
        response = requests.post(
            'https://www.odoo.com/odoo-enterprise/iot/x509',
            json={'params': {'db_uuid': db_uuid, 'enterprise_code': enterprise_code}},
            timeout=95,  # let's encrypt library timeout
        )
        response.raise_for_status()
        response_body = response.json()
    except (requests.exceptions.RequestException, ValueError) as e:
        _logger.warning("An error occurred while trying to reach odoo.com to get a new certificate: %s", e)
        if retry < 5:
            return download_odoo_certificate(retry=retry + 1)
        return _logger.exception("Maximum attempt to download the odoo.com certificate reached")

    server_error = response_body.get('error')
    if server_error:
        _logger.error("Server error received from odoo.com while trying to get the certificate: %s", server_error)
        return None

    result = response_body.get('result', {})
    certificate_error = result.get('error')
    if certificate_error:
        _logger.warning("Error received from odoo.com while trying to get the certificate: %s", certificate_error)
        return None

    update_conf({'subject': result['subject_cn']})

    certificate = result['x509_pem']
    private_key = result['private_key_pem']
    if not certificate or not private_key:  # ensure not empty strings
        _logger.error("The certificate received from odoo.com is not valid.")
        return None

    if IS_RPI:
        Path('/etc/ssl/certs/nginx-cert.crt').write_text(certificate, encoding='utf-8')
        Path('/root_bypass_ramdisks/etc/ssl/certs/nginx-cert.crt').write_text(certificate, encoding='utf-8')
        Path('/etc/ssl/private/nginx-cert.key').write_text(private_key, encoding='utf-8')
        Path('/root_bypass_ramdisks/etc/ssl/private/nginx-cert.key').write_text(private_key, encoding='utf-8')
        start_nginx_server()
        cert = x509.load_pem_x509_certificate(certificate.encode())
        if float(get_version()[1:8]) < 2025.10:
            return str(cert.not_valid_after)
        else:
            return str(cert.not_valid_after_utc)
    else:
        Path(get_path_nginx(), 'conf', 'nginx-cert.crt').write_text(certificate, encoding='utf-8')
        Path(get_path_nginx(), 'conf', 'nginx-cert.key').write_text(private_key, encoding='utf-8')
        odoo_restart(3)
        return None