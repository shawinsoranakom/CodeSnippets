def _get_sequence_values(self, name=False, code=False):
        """ Each picking type is created with a sequence. This method returns
        the sequence values associated to each picking type.
        """
        name = name if name else self.name
        code = code if code else self.code
        return {
            'in_type_id': {
                'name': _('%(name)s Sequence in', name=name),
                'prefix': code + '/' + (self.in_type_id.sequence_code or 'IN') + '/', 'padding': 5,
                'company_id': self.company_id.id,
            },
            'out_type_id': {
                'name': _('%(name)s Sequence out', name=name),
                'prefix': code + '/' + (self.out_type_id.sequence_code or 'OUT') + '/', 'padding': 5,
                'company_id': self.company_id.id,
            },
            'pack_type_id': {
                'name': _('%(name)s Sequence packing', name=name),
                'prefix': code + '/' + (self.pack_type_id.sequence_code or 'PACK') + '/', 'padding': 5,
                'company_id': self.company_id.id,
            },
            'pick_type_id': {
                'name': _('%(name)s Sequence picking', name=name),
                'prefix': code + '/' + (self.pick_type_id.sequence_code or 'PICK') + '/', 'padding': 5,
                'company_id': self.company_id.id,
            },
            'qc_type_id': {
                'name': _('%(name)s Sequence quality control', name=name),
                'prefix': code + '/' + (self.qc_type_id.sequence_code or 'QC') + '/', 'padding': 5,
                'company_id': self.company_id.id,
            },
            'store_type_id': {
                'name': _('%(name)s Sequence storage', name=name),
                'prefix': code + '/' + (self.store_type_id.sequence_code or 'STOR') + '/', 'padding': 5,
                'company_id': self.company_id.id,
            },
            'int_type_id': {
                'name': _('%(name)s Sequence internal', name=name),
                'prefix': code + '/' + (self.int_type_id.sequence_code or 'INT') + '/', 'padding': 5,
                'company_id': self.company_id.id,
            },
            'xdock_type_id': {
                'name': _('%(name)s Sequence cross dock', name=name),
                'prefix': code + '/' + (self.xdock_type_id.sequence_code or 'XD') + '/', 'padding': 5,
                'company_id': self.company_id.id,
            },
        }