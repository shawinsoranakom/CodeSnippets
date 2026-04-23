def from_url(url: str, timeout: int = 10) -> Optional["SSLCertificate"]:
        """
        Create SSLCertificate instance from a URL. Fetches cert info and initializes.
        (Fetching logic remains the same)
        """
        cert_info_raw = None # Variable to hold the fetched dict
        try:
            hostname = urlparse(url).netloc
            if ":" in hostname:
                hostname = hostname.split(":")[0]

            context = ssl.create_default_context()
            # Set check_hostname to False and verify_mode to CERT_NONE temporarily
            # for potentially problematic certificates during fetch, but parse the result regardless.
            # context.check_hostname = False
            # context.verify_mode = ssl.CERT_NONE

            with socket.create_connection((hostname, 443), timeout=timeout) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert_binary = ssock.getpeercert(binary_form=True)
                    if not cert_binary:
                         print(f"Warning: No certificate returned for {hostname}")
                         return None

                    x509 = OpenSSL.crypto.load_certificate(
                        OpenSSL.crypto.FILETYPE_ASN1, cert_binary
                    )

                    # Create the dictionary directly
                    cert_info_raw = {
                        "subject": dict(x509.get_subject().get_components()),
                        "issuer": dict(x509.get_issuer().get_components()),
                        "version": x509.get_version(),
                        "serial_number": hex(x509.get_serial_number()),
                        "not_before": x509.get_notBefore(), # Keep as bytes initially, _decode handles it
                        "not_after": x509.get_notAfter(),   # Keep as bytes initially
                        "fingerprint": x509.digest("sha256").hex(), # hex() is already string
                        "signature_algorithm": x509.get_signature_algorithm(), # Keep as bytes
                        "raw_cert": base64.b64encode(cert_binary), # Base64 is bytes, _decode handles it
                    }

                    # Add extensions
                    extensions = []
                    for i in range(x509.get_extension_count()):
                        ext = x509.get_extension(i)
                        # get_short_name() returns bytes, str(ext) handles value conversion
                        extensions.append(
                            {"name": ext.get_short_name(), "value": str(ext)}
                        )
                    cert_info_raw["extensions"] = extensions

        except ssl.SSLCertVerificationError as e:
             print(f"SSL Verification Error for {url}: {e}")
             # Decide if you want to proceed or return None based on your needs
             # You might try fetching without verification here if needed, but be cautious.
             return None
        except socket.gaierror:
            print(f"Could not resolve hostname: {hostname}")
            return None
        except socket.timeout:
            print(f"Connection timed out for {url}")
            return None
        except Exception as e:
            print(f"Error fetching/processing certificate for {url}: {e}")
            # Log the full error details if needed: logging.exception("Cert fetch error")
            return None

        # If successful, create the SSLCertificate instance from the dictionary
        if cert_info_raw:
             return SSLCertificate(cert_info_raw)
        else:
             return None