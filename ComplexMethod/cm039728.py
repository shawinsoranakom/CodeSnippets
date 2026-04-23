def encode_data(self, data, attributes):
        num_attributes = len(attributes)
        new_data = []
        current_row = 0

        row = data.row
        col = data.col
        data = data.data

        # Check if the rows are sorted
        if not all(row[i] <= row[i + 1] for i in range(len(row) - 1)):
            raise ValueError("liac-arff can only output COO matrices with "
                             "sorted rows.")

        for v, col, row in zip(data, col, row):
            if row > current_row:
                # Add empty rows if necessary
                while current_row < row:
                    yield " ".join(["{", ','.join(new_data), "}"])
                    new_data = []
                    current_row += 1

            if col >= num_attributes:
                raise BadObject(
                    'Instance %d has at least %d attributes, expected %d' %
                    (current_row, col + 1, num_attributes)
                )

            if v is None or v == '' or v != v:
                s = '?'
            else:
                s = encode_string(str(v))
            new_data.append("%d %s" % (col, s))

        yield " ".join(["{", ','.join(new_data), "}"])