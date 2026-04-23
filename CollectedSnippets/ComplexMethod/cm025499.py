async def send_file(self, timeout=None):
            """Send file via XMPP.

            Send XMPP file message using OOB (XEP_0066) and
            HTTP Upload (XEP_0363)
            """
            try:
                # Uploading with XEP_0363
                _LOGGER.debug("Timeout set to %ss", timeout)
                url = await self.upload_file(timeout=timeout)

                _LOGGER.debug("Upload success")
                for recipient in recipients:
                    if room:
                        _LOGGER.debug("Sending file to %s", room)
                        message = self.Message(sto=room, stype="groupchat")
                    else:
                        _LOGGER.debug("Sending file to %s", recipient)
                        message = self.Message(sto=recipient, stype="chat")
                    message["body"] = url
                    message["oob"]["url"] = url
                    try:
                        message.send()
                    except (IqError, IqTimeout, XMPPError) as ex:
                        _LOGGER.error("Could not send image message %s", ex)
                    if room:
                        break
            except (IqError, IqTimeout, XMPPError) as ex:
                _LOGGER.error("Upload error, could not send message %s", ex)
            except NotConnectedError as ex:
                _LOGGER.error("Connection error %s", ex)
            except FileTooBig as ex:
                _LOGGER.error("File too big for server, could not upload file %s", ex)
            except UploadServiceNotFound as ex:
                _LOGGER.error("UploadServiceNotFound, could not upload file %s", ex)
            except FileUploadError as ex:
                _LOGGER.error("FileUploadError, could not upload file %s", ex)
            except requests.exceptions.SSLError as ex:
                _LOGGER.error("Cannot establish SSL connection %s", ex)
            except requests.exceptions.ConnectionError as ex:
                _LOGGER.error("Cannot connect to server %s", ex)
            except (
                FileNotFoundError,
                PermissionError,
                IsADirectoryError,
                TimeoutError,
            ) as ex:
                _LOGGER.error("Error reading file %s", ex)
            except FutTimeoutError as ex:
                _LOGGER.error("The server did not respond in time, %s", ex)