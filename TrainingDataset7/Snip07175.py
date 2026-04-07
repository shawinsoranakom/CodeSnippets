def import_xml(self, xml):
        "Import the Spatial Reference from an XML string."
        capi.from_xml(self.ptr, xml)