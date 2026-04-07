def assertIdTypeEqualsFkType():
            with connection.cursor() as cursor:
                id_type, id_null = [
                    (c.type_code, c.null_ok)
                    for c in connection.introspection.get_table_description(
                        cursor, "test_alflpkfk_pony"
                    )
                    if c.name == "id"
                ][0]
                fk_type, fk_null = [
                    (c.type_code, c.null_ok)
                    for c in connection.introspection.get_table_description(
                        cursor, "test_alflpkfk_rider"
                    )
                    if c.name == "pony_id"
                ][0]
                m2m_fk_type, m2m_fk_null = [
                    (c.type_code, c.null_ok)
                    for c in connection.introspection.get_table_description(
                        cursor,
                        "test_alflpkfk_pony_stables",
                    )
                    if c.name == "pony_id"
                ][0]
                remote_m2m_fk_type, remote_m2m_fk_null = [
                    (c.type_code, c.null_ok)
                    for c in connection.introspection.get_table_description(
                        cursor,
                        "test_alflpkfk_stable_ponies",
                    )
                    if c.name == "pony_id"
                ][0]
            self.assertEqual(id_type, fk_type)
            self.assertEqual(id_type, m2m_fk_type)
            self.assertEqual(id_type, remote_m2m_fk_type)
            self.assertEqual(id_null, fk_null)
            self.assertEqual(id_null, m2m_fk_null)
            self.assertEqual(id_null, remote_m2m_fk_null)