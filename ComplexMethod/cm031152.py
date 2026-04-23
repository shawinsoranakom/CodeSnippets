def getFeature(self, name):
        xname = _name_xform(name)
        try:
            return getattr(self._options, xname)
        except AttributeError:
            if name == "infoset":
                options = self._options
                return (options.datatype_normalization
                        and options.whitespace_in_element_content
                        and options.comments
                        and options.charset_overrides_xml_encoding
                        and not (options.namespace_declarations
                                 or options.validate_if_schema
                                 or options.create_entity_ref_nodes
                                 or options.entities
                                 or options.cdata_sections))
            raise xml.dom.NotFoundErr("feature %s not known" % repr(name))