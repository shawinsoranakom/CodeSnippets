def _validate_hosts(self, attribute, name, value):
        # Only validate 'hosts' if a value was passed in to original data set.
        if 'hosts' in self._ds:
            if not value:
                raise AnsibleParserError("Hosts list cannot be empty. Please check your playbook")

            if is_sequence(value):
                # Make sure each item in the sequence is a valid string
                for entry in value:
                    if entry is None:
                        raise AnsibleParserError("Hosts list cannot contain values of 'None'. Please check your playbook")
                    elif not isinstance(entry, (bytes, str)):
                        raise AnsibleParserError("Hosts list contains an invalid host value: '{host!s}'".format(host=entry))

            elif not isinstance(value, (bytes, str, EncryptedString)):
                raise AnsibleParserError("Hosts list must be a sequence or string. Please check your playbook.")