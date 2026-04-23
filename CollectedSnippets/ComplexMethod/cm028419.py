def _set(self, k, v):
    """Overrides same method in ParamsDict.

    Also called by ParamsDict methods.

    Args:
      k: key to set.
      v: value.

    Raises:
      RuntimeError
    """
    subconfig_type = self._get_subconfig_type(k)

    def is_null(k):
      if k not in self.__dict__ or not self.__dict__[k]:
        return True
      return False

    if isinstance(v, dict):
      if is_null(k):
        # If the key not exist or the value is None, a new Config-family object
        # sould be created for the key.
        self.__dict__[k] = subconfig_type(v)
      elif hasattr(self.__dict__[k], 'override'):
        self.__dict__[k].override(v)
      else:
        # The key exists but it cannot be overridden. For example, it's a str.
        self.__dict__[k] = subconfig_type(v)
    elif not is_null(k) and isinstance(v, self.SEQUENCE_TYPES) and all(
        [not isinstance(e, self.IMMUTABLE_TYPES) for e in v]):
      if len(self.__dict__[k]) == len(v):
        for i in range(len(v)):
          self.__dict__[k][i].override(v[i])
      elif not all([isinstance(e, self.IMMUTABLE_TYPES) for e in v]):
        logging.warning(
            "The list/tuple don't match the value dictionaries provided. Thus, "
            'the list/tuple is determined by the type annotation and '
            'values provided. This is error-prone.')
        self.__dict__[k] = self._import_config(v, subconfig_type)
      else:
        self.__dict__[k] = self._import_config(v, subconfig_type)
    else:
      self.__dict__[k] = self._import_config(v, subconfig_type)