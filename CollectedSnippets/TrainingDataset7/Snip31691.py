def test_crafted_xml_rejected(self):
        depth = 100
        leaf_text_len = 1000
        nested_open = "<nested>" * depth
        nested_close = "</nested>" * depth
        leaf = "x" * leaf_text_len
        field_content = f"{nested_open}{leaf}{nested_close}"
        crafted_xml = textwrap.dedent(f"""
        <django-objects version="1.0">
            <object model="contenttypes.contenttype" pk="1">
                <field name="app_label">{field_content}</field>
                <field name="model">m</field>
            </object>
        </django-objects>""")

        msg = "Unexpected element: 'nested'"
        with self.assertRaisesMessage(SuspiciousOperation, msg):
            list(XMLDeserializer(crafted_xml))