def button_confirm_login(self):
        for server in self:
            connection = None
            try:
                connection = server._connect__(allow_archived=True)
                server.write({'state': 'done'})
            except UnicodeError as e:
                raise UserError(_("Invalid server name!\n %s", tools.exception_to_unicode(e)))
            except (gaierror, timeout, IMAP4.abort) as e:
                raise UserError(_("No response received. Check server information.\n %s", tools.exception_to_unicode(e)))
            except (IMAP4.error, poplib.error_proto) as err:
                raise UserError(_("Server replied with following exception:\n %s", tools.exception_to_unicode(err)))
            except SSLError as e:
                raise UserError(_("An SSL exception occurred. Check SSL/TLS configuration on server port.\n %s", tools.exception_to_unicode(e)))
            except (OSError, Exception) as err:
                _logger.info("Failed to connect to %s server %s.", server.server_type, server.name, exc_info=True)
                raise UserError(_("Connection test failed: %s", tools.exception_to_unicode(err)))
            finally:
                try:
                    if connection:
                        connection.disconnect()
                except Exception:
                    # ignored, just a consequence of the previous exception
                    pass
        return True