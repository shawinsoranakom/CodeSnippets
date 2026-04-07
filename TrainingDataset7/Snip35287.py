def test_simple_equal_raises_message(self):
        xml1 = "<elem attr1='a' />"
        xml2 = "<elem attr2='b' attr1='a' />"

        msg = """{xml1} != {xml2}
- <elem attr1='a' />
+ <elem attr2='b' attr1='a' />
?      ++++++++++
""".format(xml1=repr(xml1), xml2=repr(xml2))

        with self.assertRaisesMessage(AssertionError, msg):
            self.assertXMLEqual(xml1, xml2)