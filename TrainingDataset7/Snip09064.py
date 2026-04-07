def m2m_convert(n):
                keys = n.getElementsByTagName("natural")
                if keys:
                    # If there are 'natural' subelements, it must be a natural
                    # key
                    field_value = []
                    for k in keys:
                        if k.getElementsByTagName("None"):
                            field_value.append(None)
                        else:
                            field_value.append(getInnerText(k).strip())
                    obj_pk = (
                        default_manager.db_manager(self.db)
                        .get_by_natural_key(*field_value)
                        .pk
                    )
                else:
                    # Otherwise, treat like a normal PK value.
                    obj_pk = model._meta.pk.to_python(n.getAttribute("pk"))
                return obj_pk