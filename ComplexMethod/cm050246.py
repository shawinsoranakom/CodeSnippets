def _build_display_name(self, *args, max_length=34, should_pad=True, **kwargs):
        """ Build a token name of the desired maximum length with the format `•••• 1234`.

        The payment details are padded on the left with up to four padding characters. The padding
        is only added if there is enough room for it. If not, it is either reduced or not added at
        all. If there is not enough room for the payment details either, they are trimmed from the
        left.

        For a module to customize the display name of a token, it must override this method and
        return the customized display name.

        Note: `self.ensure_one()`

        :param list args: The arguments passed by QWeb when calling this method.
        :param int max_length: The desired maximum length of the token name. The default is `34` to
                               fit the largest IBANs.
        :param bool should_pad: Whether the token should be padded.
        :param dict kwargs: Optional data used in overrides of this method.
        :return: The padded token name.
        :rtype: str
        """
        self.ensure_one()

        if not self.create_date:
            return ''

        padding_length = max_length - len(self.payment_details or '')
        if not self.payment_details:
            create_date_str = self.create_date.strftime('%Y/%m/%d')
            display_name = _("Payment details saved on %(date)s", date=create_date_str)
        elif padding_length >= 2:  # Enough room for padding.
            padding = '•' * min(padding_length - 1, 4) + ' ' if should_pad else ''
            display_name = ''.join([padding, self.payment_details])
        elif padding_length > 0:  # Not enough room for padding.
            display_name = self.payment_details
        else:  # Not enough room for neither padding nor the payment details.
            display_name = self.payment_details[-max_length:] if max_length > 0 else ''
        return display_name