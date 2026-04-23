def test_serialization(self):
        "m2m-through models aren't serialized as m2m fields. Refs #8134"
        pks = {
            "p_pk": self.bob.pk,
            "g_pk": self.roll.pk,
            "m_pk": self.bob_roll.pk,
            "app_label": "m2m_through_regress",
        }

        out = StringIO()
        management.call_command(
            "dumpdata", "m2m_through_regress", format="json", stdout=out
        )
        self.assertJSONEqual(
            out.getvalue().strip(),
            '[{"pk": %(m_pk)s, "model": "m2m_through_regress.membership", '
            '"fields": {"person": %(p_pk)s, "price": 100, "group": %(g_pk)s}}, '
            '{"pk": %(p_pk)s, "model": "m2m_through_regress.person", '
            '"fields": {"name": "Bob"}}, '
            '{"pk": %(g_pk)s, "model": "m2m_through_regress.group", '
            '"fields": {"name": "Roll"}}]' % pks,
        )

        out = StringIO()
        management.call_command(
            "dumpdata", "m2m_through_regress", format="xml", indent=2, stdout=out
        )
        self.assertXMLEqual(
            out.getvalue().strip(),
            """
<?xml version="1.0" encoding="utf-8"?>
<django-objects version="1.0">
  <object pk="%(m_pk)s" model="%(app_label)s.membership">
    <field to="%(app_label)s.person" name="person" rel="ManyToOneRel">%(p_pk)s</field>
    <field to="%(app_label)s.group" name="group" rel="ManyToOneRel">%(g_pk)s</field>
    <field type="IntegerField" name="price">100</field>
  </object>
  <object pk="%(p_pk)s" model="%(app_label)s.person">
    <field type="CharField" name="name">Bob</field>
  </object>
  <object pk="%(g_pk)s" model="%(app_label)s.group">
    <field type="CharField" name="name">Roll</field>
  </object>
</django-objects>
        """.strip() % pks,
        )