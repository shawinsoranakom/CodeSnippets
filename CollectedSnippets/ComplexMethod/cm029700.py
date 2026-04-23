def send_message(self, msg, from_addr=None, to_addrs=None,
                     mail_options=(), rcpt_options=()):
        """Converts message to a bytestring and passes it to sendmail.

        The arguments are as for sendmail, except that msg is an
        email.message.Message object.  If from_addr is None or to_addrs is
        None, these arguments are taken from the headers of the Message as
        described in RFC 5322 (a ValueError is raised if there is more than
        one set of 'Resent-' headers).  Regardless of the values of from_addr and
        to_addr, any Bcc field (or Resent-Bcc field, when the Message is a
        resent) of the Message object won't be transmitted.  The Message
        object is then serialized using email.generator.BytesGenerator and
        sendmail is called to transmit the message.  If the sender or any of
        the recipient addresses contain non-ASCII and the server advertises the
        SMTPUTF8 capability, the policy is cloned with utf8 set to True for the
        serialization, and SMTPUTF8 and BODY=8BITMIME are asserted on the send.
        If the server does not support SMTPUTF8, an SMTPNotSupported error is
        raised.  Otherwise the generator is called without modifying the
        policy.

        """
        # 'Resent-Date' is a mandatory field if the Message is resent (RFC 5322
        # Section 3.6.6). In such a case, we use the 'Resent-*' fields.  However,
        # if there is more than one 'Resent-' block there's no way to
        # unambiguously determine which one is the most recent in all cases,
        # so rather than guess we raise a ValueError in that case.
        #
        # TODO implement heuristics to guess the correct Resent-* block with an
        # option allowing the user to enable the heuristics.  (It should be
        # possible to guess correctly almost all of the time.)

        self.ehlo_or_helo_if_needed()
        resent = msg.get_all('Resent-Date')
        if resent is None:
            header_prefix = ''
        elif len(resent) == 1:
            header_prefix = 'Resent-'
        else:
            raise ValueError("message has more than one 'Resent-' header block")
        if from_addr is None:
            # Prefer the sender field per RFC 5322 section 3.6.2.
            from_addr = (msg[header_prefix + 'Sender']
                           if (header_prefix + 'Sender') in msg
                           else msg[header_prefix + 'From'])
            from_addr = email.utils.getaddresses([from_addr])[0][1]
        if to_addrs is None:
            addr_fields = [f for f in (msg[header_prefix + 'To'],
                                       msg[header_prefix + 'Bcc'],
                                       msg[header_prefix + 'Cc'])
                           if f is not None]
            to_addrs = [a[1] for a in email.utils.getaddresses(addr_fields)]
        # Make a local copy so we can delete the bcc headers.
        msg_copy = copy.copy(msg)
        del msg_copy['Bcc']
        del msg_copy['Resent-Bcc']
        international = False
        try:
            ''.join([from_addr, *to_addrs]).encode('ascii')
        except UnicodeEncodeError:
            if not self.has_extn('smtputf8'):
                raise SMTPNotSupportedError(
                    "One or more source or delivery addresses require"
                    " internationalized email support, but the server"
                    " does not advertise the required SMTPUTF8 capability")
            international = True
        with io.BytesIO() as bytesmsg:
            if international:
                g = email.generator.BytesGenerator(
                    bytesmsg, policy=msg.policy.clone(utf8=True))
                mail_options = (*mail_options, 'SMTPUTF8', 'BODY=8BITMIME')
            else:
                g = email.generator.BytesGenerator(bytesmsg)
            g.flatten(msg_copy, linesep='\r\n')
            flatmsg = bytesmsg.getvalue()
        return self.sendmail(from_addr, to_addrs, flatmsg, mail_options,
                             rcpt_options)