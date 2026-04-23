async def run(
        self, input_data: Input, *, credentials: SMTPCredentials, **kwargs
    ) -> BlockOutput:
        try:
            # --- SSRF Protection ---
            smtp_port = input_data.config.smtp_port
            if smtp_port not in self.ALLOWED_SMTP_PORTS:
                yield "error", (
                    f"SMTP port {smtp_port} is not allowed. "
                    f"Allowed ports: {sorted(self.ALLOWED_SMTP_PORTS)}"
                )
                return

            await resolve_and_check_blocked(input_data.config.smtp_server)

            status = self.send_email(
                config=input_data.config,
                to_email=input_data.to_email,
                subject=input_data.subject,
                body=input_data.body,
                credentials=credentials,
            )
            yield "status", status
        except socket.gaierror:
            yield "error", (
                f"Cannot connect to SMTP server '{input_data.config.smtp_server}'. "
                "Please verify the server address is correct."
            )
        except socket.timeout:
            yield "error", (
                f"Connection timeout to '{input_data.config.smtp_server}' "
                f"on port {input_data.config.smtp_port}. "
                "The server may be down or unreachable."
            )
        except ConnectionRefusedError:
            yield "error", (
                f"Connection refused to '{input_data.config.smtp_server}' "
                f"on port {input_data.config.smtp_port}. "
                "Common SMTP ports are: 587 (TLS), 465 (SSL), 25 (plain). "
                "Please verify the port is correct."
            )
        except smtplib.SMTPNotSupportedError:
            yield "error", (
                f"STARTTLS not supported by server '{input_data.config.smtp_server}'. "
                "Try using port 465 for SSL or port 25 for unencrypted connection."
            )
        except ssl.SSLError as e:
            yield "error", (
                f"SSL/TLS error when connecting to '{input_data.config.smtp_server}': {str(e)}. "
                "The server may require a different security protocol."
            )
        except smtplib.SMTPAuthenticationError:
            yield "error", (
                "Authentication failed. Please verify your username and password are correct."
            )
        except smtplib.SMTPRecipientsRefused:
            yield "error", (
                f"Recipient email address '{input_data.to_email}' was rejected by the server. "
                "Please verify the email address is valid."
            )
        except smtplib.SMTPSenderRefused:
            yield "error", (
                "Sender email address defined in the credentials that where used"
                "was rejected by the server. "
                "Please verify your account is authorized to send emails."
            )
        except smtplib.SMTPConnectError:
            yield "error", (
                f"Cannot connect to SMTP server '{input_data.config.smtp_server}' "
                f"on port {input_data.config.smtp_port}."
            )
        except smtplib.SMTPServerDisconnected:
            yield "error", (
                f"SMTP server '{input_data.config.smtp_server}' "
                "disconnected unexpectedly."
            )
        except smtplib.SMTPDataError as e:
            yield "error", f"Email data rejected by server: {str(e)}"
        except ValueError as e:
            yield "error", str(e)
        except Exception as e:
            raise e