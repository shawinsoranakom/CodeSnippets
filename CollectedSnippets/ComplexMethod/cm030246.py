def has_header(self, sample):
        # Creates a dictionary of types of data in each column. If any
        # column is of a single type (say, integers), *except* for the first
        # row, then the first row is presumed to be labels. If the type
        # can't be determined, it is assumed to be a string in which case
        # the length of the string is the determining factor: if all of the
        # rows except for the first are the same length, it's a header.
        # Finally, a 'vote' is taken at the end for each column, adding or
        # subtracting from the likelihood of the first row being a header.

        rdr = reader(StringIO(sample), self.sniff(sample))

        header = next(rdr) # assume first row is header

        columns = len(header)
        columnTypes = {}
        for i in range(columns): columnTypes[i] = None

        checked = 0
        for row in rdr:
            # arbitrary number of rows to check, to keep it sane
            if checked > 20:
                break
            checked += 1

            if len(row) != columns:
                continue # skip rows that have irregular number of columns

            for col in list(columnTypes.keys()):
                thisType = complex
                try:
                    thisType(row[col])
                except (ValueError, OverflowError):
                    # fallback to length of string
                    thisType = len(row[col])

                if thisType != columnTypes[col]:
                    if columnTypes[col] is None: # add new column type
                        columnTypes[col] = thisType
                    else:
                        # type is inconsistent, remove column from
                        # consideration
                        del columnTypes[col]

        # finally, compare results against first row and "vote"
        # on whether it's a header
        hasHeader = 0
        for col, colType in columnTypes.items():
            if isinstance(colType, int): # it's a length
                if len(header[col]) != colType:
                    hasHeader += 1
                else:
                    hasHeader -= 1
            else: # attempt typecast
                try:
                    colType(header[col])
                except (ValueError, TypeError):
                    hasHeader += 1
                else:
                    hasHeader -= 1

        return hasHeader > 0