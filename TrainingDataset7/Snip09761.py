def _alter_field_type_workaround(self, model, old_field, new_field):
        """
        Oracle refuses to change from some type to other type.
        What we need to do instead is:
        - Add a nullable version of the desired field with a temporary name. If
          the new column is an auto field, then the temporary column can't be
          nullable.
        - Update the table to transfer values from old to new
        - Drop old column
        - Rename the new column and possibly drop the nullable property
        """
        # Make a new field that's like the new one but with a temporary
        # column name.
        new_temp_field = copy.deepcopy(new_field)
        new_temp_field.null = new_field.get_internal_type() not in (
            "AutoField",
            "BigAutoField",
            "SmallAutoField",
        )
        new_temp_field.column = self._generate_temp_name(new_field.column)
        # Add it
        self.add_field(model, new_temp_field)
        # Explicit data type conversion
        # https://docs.oracle.com/en/database/oracle/oracle-database/21/sqlrf
        # /Data-Type-Comparison-Rules.html#GUID-D0C5A47E-6F93-4C2D-9E49-4F2B86B359DD
        new_value = self.quote_name(old_field.column)
        old_type = old_field.db_type(self.connection)
        if re.match("^N?CLOB", old_type):
            new_value = "TO_CHAR(%s)" % new_value
            old_type = "VARCHAR2"
        if re.match("^N?VARCHAR2", old_type):
            new_internal_type = new_field.get_internal_type()
            if new_internal_type == "DateField":
                new_value = "TO_DATE(%s, 'YYYY-MM-DD')" % new_value
            elif new_internal_type == "DateTimeField":
                new_value = "TO_TIMESTAMP(%s, 'YYYY-MM-DD HH24:MI:SS.FF')" % new_value
            elif new_internal_type == "TimeField":
                # TimeField are stored as TIMESTAMP with a 1900-01-01 date
                # part.
                new_value = "CONCAT('1900-01-01 ', %s)" % new_value
                new_value = "TO_TIMESTAMP(%s, 'YYYY-MM-DD HH24:MI:SS.FF')" % new_value
        # Transfer values across
        self.execute(
            "UPDATE %s set %s=%s"
            % (
                self.quote_name(model._meta.db_table),
                self.quote_name(new_temp_field.column),
                new_value,
            )
        )
        # Drop the old field
        self.remove_field(model, old_field)
        # Rename and possibly make the new field NOT NULL
        super().alter_field(model, new_temp_field, new_field)
        # Recreate foreign key (if necessary) because the old field is not
        # passed to the alter_field() and data types of new_temp_field and
        # new_field always match.
        new_type = new_field.db_type(self.connection)
        if (
            (old_field.primary_key and new_field.primary_key)
            or (old_field.unique and new_field.unique)
        ) and old_type != new_type:
            for _, rel in _related_non_m2m_objects(new_temp_field, new_field):
                if rel.field.db_constraint:
                    self.execute(
                        self._create_fk_sql(rel.related_model, rel.field, "_fk")
                    )