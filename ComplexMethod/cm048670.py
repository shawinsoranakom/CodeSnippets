def _calculate_hashes(self, previous_hash):
        """
        :return: dict of move_id: hash
        """
        hash_version = self.env.context.get('hash_version', MAX_HASH_VERSION)

        def _getattrstring(obj, field_name):
            field_value = obj[field_name]
            if obj._fields[field_name].type == 'many2one':
                field_value = field_value.id
            if obj._fields[field_name].type == 'monetary' and hash_version >= 3:
                return float_repr(field_value, obj.currency_id.decimal_places)
            return str(field_value)

        move2hash = {}
        previous_hash = previous_hash or ''

        for move in self:
            if previous_hash and previous_hash.startswith("$"):
                previous_hash = previous_hash.split("$")[2]  # The hash version is not used for the computation of the next hash
            values = {}
            for fname in move._get_integrity_hash_fields():
                values[fname] = _getattrstring(move, fname)

            for line in move.line_ids:
                for fname in line._get_integrity_hash_fields():
                    k = 'line_%d_%s' % (line.id, fname)
                    values[k] = _getattrstring(line, fname)
            current_record = dumps(values, sort_keys=True, ensure_ascii=True, indent=None, separators=(',', ':'))
            hash_string = sha256((previous_hash + current_record).encode('utf-8')).hexdigest()
            move2hash[move] = f"${hash_version}${hash_string}" if hash_version >= 4 else hash_string
            previous_hash = move2hash[move]
        return move2hash