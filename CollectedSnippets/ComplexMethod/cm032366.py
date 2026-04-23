def _invoke(self, **kwargs):
        if self.check_if_canceled("Email processing"):
            return

        if not kwargs.get("to_email"):
            self.set_output("success", False)
            return ""

        last_e = ""
        for _ in range(self._param.max_retries+1):
            if self.check_if_canceled("Email processing"):
                return

            try:
                # Parse JSON string passed from upstream
                email_data = kwargs

                # Validate required fields
                if "to_email" not in email_data:
                    self.set_output("_ERROR", "Missing required field: to_email")
                    self.set_output("success", False)
                    return False

                # Create email object
                msg = MIMEMultipart('alternative')

                # Properly handle sender name encoding
                msg['From'] = formataddr((str(Header(self._param.sender_name,'utf-8')), self._param.email))
                msg['To'] = email_data["to_email"]
                if email_data.get("cc_email"):
                    msg['Cc'] = email_data["cc_email"]
                msg['Subject'] = Header(email_data.get("subject", "No Subject"), 'utf-8').encode()

                # Use content from email_data or default content
                email_content = email_data.get("content", "No content provided")
                # msg.attach(MIMEText(email_content, 'plain', 'utf-8'))
                msg.attach(MIMEText(email_content, 'html', 'utf-8'))

                # Connect to SMTP server and send
                logging.info(f"Connecting to SMTP server {self._param.smtp_server}:{self._param.smtp_port}")

                if self.check_if_canceled("Email processing"):
                    return

                context = smtplib.ssl.create_default_context()
                with smtplib.SMTP(self._param.smtp_server, self._param.smtp_port) as server:
                    server.ehlo()
                    server.starttls(context=context)
                    server.ehlo()

                    # Login
                    smtp_username = self._param.smtp_username or self._param.email
                    logging.info(f"Attempting to login with username: {smtp_username}")
                    server.login(smtp_username, self._param.password)

                    # Get all recipient list
                    recipients = [email_data["to_email"]]
                    if email_data.get("cc_email"):
                        recipients.extend(email_data["cc_email"].split(','))

                    # Send email
                    logging.info(f"Sending email to recipients: {recipients}")

                    if self.check_if_canceled("Email processing"):
                        return

                    try:
                        server.send_message(msg, self._param.email, recipients)
                        success = True
                    except Exception as e:
                        logging.error(f"Error during send_message: {str(e)}")
                        # Try alternative method
                        server.sendmail(self._param.email, recipients, msg.as_string())
                        success = True

                    try:
                        server.quit()
                    except Exception as e:
                        # Ignore errors when closing connection
                        logging.warning(f"Non-fatal error during connection close: {str(e)}")

                self.set_output("success", success)
                return success

            except json.JSONDecodeError:
                error_msg = "Invalid JSON format in input"
                logging.error(error_msg)
                self.set_output("_ERROR", error_msg)
                self.set_output("success", False)
                return False

            except smtplib.SMTPAuthenticationError:
                error_msg = "SMTP Authentication failed. Please check your SMTP username(email) and authorization code."
                logging.error(error_msg)
                self.set_output("_ERROR", error_msg)
                self.set_output("success", False)
                return False

            except smtplib.SMTPConnectError:
                error_msg = f"Failed to connect to SMTP server {self._param.smtp_server}:{self._param.smtp_port}"
                logging.error(error_msg)
                last_e = error_msg
                time.sleep(self._param.delay_after_error)

            except smtplib.SMTPException as e:
                error_msg = f"SMTP error occurred: {str(e)}"
                logging.error(error_msg)
                last_e = error_msg
                time.sleep(self._param.delay_after_error)

            except Exception as e:
                error_msg = f"Unexpected error: {str(e)}"
                logging.error(error_msg)
                self.set_output("_ERROR", error_msg)
                self.set_output("success", False)
                return False

        if last_e:
            self.set_output("_ERROR", str(last_e))
            return False

        assert False, self.output()