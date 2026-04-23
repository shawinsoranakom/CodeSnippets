def _override(self, override_dict, is_strict=True):
    """Overrides same method in ParamsDict.

    Also called by ParamsDict methods.

    Args:
      override_dict: dictionary to write to .
      is_strict: If True, not allows to add new keys.

    Raises:
      KeyError: overriding reserved keys or keys not exist (is_strict=True).
    """
    for k, v in sorted(override_dict.items()):
      if k in self.RESERVED_ATTR:
        raise KeyError('The key {!r} is internally reserved. '
                       'Can not be overridden.'.format(k))
      if k not in self.__dict__:
        if is_strict:
          raise KeyError('The key {!r} does not exist in {!r}. '
                         'To extend the existing keys, use '
                         '`override` with `is_strict` = False.'.format(
                             k, type(self)))
        else:
          self._set(k, v)
      else:
        if isinstance(v, dict) and hasattr(self.__dict__[k], '_override'):
          self.__dict__[k]._override(v, is_strict)  # pylint: disable=protected-access
        elif isinstance(v, params_dict.ParamsDict) and hasattr(
            self.__dict__[k], '_override'
        ):
          self.__dict__[k]._override(v.as_dict(), is_strict)  # pylint: disable=protected-access
        else:
          self._set(k, v)