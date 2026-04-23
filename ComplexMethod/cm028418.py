def validate(self):
    """Validate the parameters consistency based on the restrictions.

    This method validates the internal consistency using the pre-defined list of
    restrictions. A restriction is defined as a string which specifies a binary
    operation. The supported binary operations are {'==', '!=', '<', '<=', '>',
    '>='}. Note that the meaning of these operators are consistent with the
    underlying Python immplementation. Users should make sure the define
    restrictions on their type make sense.

    For example, for a ParamsDict like the following
    ```
    a:
      a1: 1
      a2: 2
    b:
      bb:
        bb1: 10
        bb2: 20
      ccc:
        a1: 1
        a3: 3
    ```
    one can define two restrictions like this
    ['a.a1 == b.ccc.a1', 'a.a2 <= b.bb.bb2']

    What it enforces are:
     - a.a1 = 1 == b.ccc.a1 = 1
     - a.a2 = 2 <= b.bb.bb2 = 20

    Raises:
      KeyError: if any of the following happens
        (1) any of parameters in any of restrictions is not defined in
            ParamsDict,
        (2) any inconsistency violating the restriction is found.
      ValueError: if the restriction defined in the string is not supported.
    """

    def _get_kv(dotted_string, params_dict):
      """Get keys and values indicated by dotted_string."""
      if _CONST_VALUE_RE.match(dotted_string) is not None:
        const_str = dotted_string
        if const_str == 'None':
          constant = None
        else:
          constant = float(const_str)
        return None, constant
      else:
        tokenized_params = dotted_string.split('.')
        v = params_dict
        for t in tokenized_params:
          v = v[t]
        return tokenized_params[-1], v

    def _get_kvs(tokens, params_dict):
      if len(tokens) != 2:
        raise ValueError('Only support binary relation in restriction.')
      stripped_tokens = [t.strip() for t in tokens]
      left_k, left_v = _get_kv(stripped_tokens[0], params_dict)
      right_k, right_v = _get_kv(stripped_tokens[1], params_dict)
      return left_k, left_v, right_k, right_v

    params_dict = self.as_dict()
    for restriction in self._restrictions:
      if '==' in restriction:
        tokens = restriction.split('==')
        _, left_v, _, right_v = _get_kvs(tokens, params_dict)
        if left_v != right_v:
          raise KeyError(
              'Found inconsistency between key `{}` and key `{}`.'.format(
                  tokens[0], tokens[1]))
      elif '!=' in restriction:
        tokens = restriction.split('!=')
        _, left_v, _, right_v = _get_kvs(tokens, params_dict)
        if left_v == right_v:
          raise KeyError(
              'Found inconsistency between key `{}` and key `{}`.'.format(
                  tokens[0], tokens[1]))
      elif '<=' in restriction:
        tokens = restriction.split('<=')
        _, left_v, _, right_v = _get_kvs(tokens, params_dict)
        if left_v > right_v:
          raise KeyError(
              'Found inconsistency between key `{}` and key `{}`.'.format(
                  tokens[0], tokens[1]))
      elif '<' in restriction:
        tokens = restriction.split('<')
        _, left_v, _, right_v = _get_kvs(tokens, params_dict)
        if left_v >= right_v:
          raise KeyError(
              'Found inconsistency between key `{}` and key `{}`.'.format(
                  tokens[0], tokens[1]))
      elif '>=' in restriction:
        tokens = restriction.split('>=')
        _, left_v, _, right_v = _get_kvs(tokens, params_dict)
        if left_v < right_v:
          raise KeyError(
              'Found inconsistency between key `{}` and key `{}`.'.format(
                  tokens[0], tokens[1]))
      elif '>' in restriction:
        tokens = restriction.split('>')
        _, left_v, _, right_v = _get_kvs(tokens, params_dict)
        if left_v <= right_v:
          raise KeyError(
              'Found inconsistency between key `{}` and key `{}`.'.format(
                  tokens[0], tokens[1]))
      else:
        raise ValueError('Unsupported relation in restriction.')