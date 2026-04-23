def extra_state_attributes(self) -> dict[str, Any]:
        """Return the device specific state attributes."""
        attributes: dict[str, Any] = {}

        if self._operated_remote is not None:
            attributes[ATTR_OPERATION_REMOTE] = self._operated_remote
        if self._operated_keypad is not None:
            attributes[ATTR_OPERATION_KEYPAD] = self._operated_keypad
        if self._operated_manual is not None:
            attributes[ATTR_OPERATION_MANUAL] = self._operated_manual
        if self._operated_tag is not None:
            attributes[ATTR_OPERATION_TAG] = self._operated_tag
        if self._operated_autorelock is not None:
            attributes[ATTR_OPERATION_AUTORELOCK] = self._operated_autorelock

        if self._operated_remote:
            attributes[ATTR_OPERATION_METHOD] = OPERATION_METHOD_REMOTE
        elif self._operated_keypad:
            attributes[ATTR_OPERATION_METHOD] = OPERATION_METHOD_KEYPAD
        elif self._operated_manual:
            attributes[ATTR_OPERATION_METHOD] = OPERATION_METHOD_MANUAL
        elif self._operated_tag:
            attributes[ATTR_OPERATION_METHOD] = OPERATION_METHOD_TAG
        elif self._operated_autorelock:
            attributes[ATTR_OPERATION_METHOD] = OPERATION_METHOD_AUTORELOCK
        else:
            attributes[ATTR_OPERATION_METHOD] = OPERATION_METHOD_MOBILE_DEVICE

        return attributes