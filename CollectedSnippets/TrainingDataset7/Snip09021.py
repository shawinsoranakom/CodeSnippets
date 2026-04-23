def m2m_value(value):
                    if natural := value.natural_key():
                        return natural
                    else:
                        return self._value_from_field(value, value._meta.pk)