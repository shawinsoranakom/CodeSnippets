def unsign(self, signed_value):
        if self.sep not in signed_value:
            raise BadSignature('No "%s" found in value' % self.sep)
        value, sig = signed_value.rsplit(self.sep, 1)
        for key in [self.key, *self.fallback_keys]:
            if constant_time_compare(sig, self.signature(value, key)):
                return value
        raise BadSignature('Signature "%s" does not match' % sig)