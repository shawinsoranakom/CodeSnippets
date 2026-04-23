def bulk_insert_sql(self, fields, placeholder_rows):
        field_placeholders = [
            BulkInsertMapper.types.get(
                getattr(field, "target_field", field).get_internal_type(), "%s"
            )
            for field in fields
            if field
        ]
        query = []
        for row in placeholder_rows:
            select = []
            for i, placeholder in enumerate(row):
                # A model without any fields has fields=[None].
                if fields[i]:
                    placeholder = field_placeholders[i] % placeholder
                # Add columns aliases to the first select to avoid "ORA-00918:
                # column ambiguously defined" when two or more columns in the
                # first select have the same value.
                if not query:
                    placeholder = "%s col_%s" % (placeholder, i)
                select.append(placeholder)
            suffix = self.connection.features.bare_select_suffix
            query.append(f"SELECT %s{suffix}" % ", ".join(select))
        # Bulk insert to tables with Oracle identity columns causes Oracle to
        # add sequence.nextval to it. Sequence.nextval cannot be used with the
        # UNION operator. To prevent incorrect SQL, move UNION to a subquery.
        return "SELECT * FROM (%s)" % " UNION ALL ".join(query)