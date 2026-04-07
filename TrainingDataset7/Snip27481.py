def assertIdTypeEqualsMTIFkType():
            with connection.cursor() as cursor:
                parent_id_type = _get_column_id_type(cursor, "pony", "id")
                child_id_type = _get_column_id_type(
                    cursor, "shetlandpony", "pony_ptr_id"
                )
                mti_id_type = _get_column_id_type(cursor, "shetlandrider", "pony_id")
            self.assertEqual(parent_id_type, child_id_type)
            self.assertEqual(parent_id_type, mti_id_type)