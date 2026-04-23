def validate(self):
        '''Validate the schema:
        - verify ids on inputs and outputs are unique - both internally and in relation to each other
        '''
        nested_inputs: list[Input] = []
        for input in self.inputs:
            if not isinstance(input, DynamicInput):
                nested_inputs.extend(input.get_all())
        input_ids = [i.id for i in nested_inputs]
        output_ids = [o.id for o in self.outputs]
        input_set = set(input_ids)
        output_set = set(output_ids)
        issues: list[str] = []
        # verify ids are unique per list
        if len(input_set) != len(input_ids):
            issues.append(f"Input ids must be unique, but {[item for item, count in Counter(input_ids).items() if count > 1]} are not.")
        if len(output_set) != len(output_ids):
            issues.append(f"Output ids must be unique, but {[item for item, count in Counter(output_ids).items() if count > 1]} are not.")
        if len(issues) > 0:
            raise ValueError("\n".join(issues))
        # validate inputs and outputs
        for input in self.inputs:
            input.validate()
        for output in self.outputs:
            output.validate()
        if self.price_badge is not None:
            self.price_badge.validate()