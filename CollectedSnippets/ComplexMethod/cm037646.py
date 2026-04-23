def _validate_tfm_schemes(self, num_partitions: int):
        if len(self.input_tfms) > 0:
            if 0 not in self.input_tfms:
                raise ValueError("Must have same input")

            for part_index in range(num_partitions):
                if self.input_tfms[part_index] != self.input_tfms[0]:
                    raise ValueError("Must have same input")

        if len(self.output_tfms) > 0:
            scheme_name = list(self.output_tfms.values())[0].scheme_name
            location = list(self.output_tfms.values())[0].args.location

            for tfm in self.output_tfms.values():
                if tfm.scheme_name != scheme_name:
                    raise ValueError("Must have same scheme name")
                if tfm.args.location != location:
                    raise ValueError("Must have same location")

        return self.input_tfms, self.output_tfms