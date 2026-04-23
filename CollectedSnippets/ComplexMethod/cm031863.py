def __init__(self, version, ideograph_check=True):
        self.changed = []
        table = [None] * 0x110000
        for s in UcdFile(UNICODE_DATA, version):
            char = int(s[0], 16)
            table[char] = from_row(s)

        self.derived_name_ranges = []
        self.derived_name_prefixes = {
            prefix: i
            for i, (_, prefix) in enumerate(derived_name_range_names)
        }

        # expand first-last ranges
        field = None
        for i in range(0, 0x110000):
            # The file UnicodeData.txt has its own distinct way of
            # expressing ranges.  See:
            #   https://www.unicode.org/reports/tr44/#Code_Point_Ranges
            s = table[i]
            if s:
                if s.name[-6:] == "First>":
                    s.name = ""
                    field = dataclasses.astuple(s)[:15]
                elif s.name[-5:] == "Last>":
                    for j, (rangename, _) in enumerate(derived_name_range_names):
                        if s.name.startswith("<" + rangename):
                            self.derived_name_ranges.append(
                                (field[0], s.codepoint, j))
                            break
                    s.name = ""
                    field = None
                else:
                    codepoint = s.codepoint
                    if s.name.endswith(codepoint):
                        prefix = s.name[:-len(codepoint)]
                        j = self.derived_name_prefixes.get(prefix)
                        if j is None:
                            j = len(self.derived_name_prefixes)
                            self.derived_name_prefixes[prefix] = j
                        if (self.derived_name_ranges
                                and self.derived_name_ranges[-1][2] == j
                                and int(self.derived_name_ranges[-1][1], 16) == i - 1):
                            self.derived_name_ranges[-1][1] = codepoint
                        else:
                            self.derived_name_ranges.append(
                                [codepoint, codepoint, j])
                        s.name = ""
            elif field:
                table[i] = from_row(('%04X' % i,) + field[1:])

        # public attributes
        self.filename = UNICODE_DATA % ''
        self.table = table
        self.chars = list(range(0x110000)) # unicode 3.2

        # check for name aliases and named sequences, see #12753
        # aliases and named sequences are not in 3.2.0
        if version != '3.2.0':
            self.aliases = []
            # store aliases in the Private Use Area 15, in range U+F0000..U+F00FF,
            # in order to take advantage of the compression and lookup
            # algorithms used for the other characters
            pua_index = NAME_ALIASES_START
            for char, name, abbrev in UcdFile(NAME_ALIASES, version):
                char = int(char, 16)
                self.aliases.append((name, char))
                # also store the name in the PUA 1
                self.table[pua_index].name = name
                pua_index += 1
            assert pua_index - NAME_ALIASES_START == len(self.aliases)

            self.named_sequences = []
            # store named sequences in the PUA 1, in range U+F0100..,
            # in order to take advantage of the compression and lookup
            # algorithms used for the other characters.

            assert pua_index < NAMED_SEQUENCES_START
            pua_index = NAMED_SEQUENCES_START
            for name, chars in UcdFile(NAMED_SEQUENCES, version):
                chars = tuple(int(char, 16) for char in chars.split())
                # check that the structure defined in makeunicodename is OK
                assert 2 <= len(chars) <= 4, "change the Py_UCS2 array size"
                assert all(c <= 0xFFFF for c in chars), ("use Py_UCS4 in "
                    "the NamedSequence struct and in unicodedata_lookup")
                self.named_sequences.append((name, chars))
                # also store these in the PUA 1
                self.table[pua_index].name = name
                pua_index += 1
            assert pua_index - NAMED_SEQUENCES_START == len(self.named_sequences)

        self.exclusions = {}
        for char, in UcdFile(COMPOSITION_EXCLUSIONS, version):
            char = int(char, 16)
            self.exclusions[char] = 1

        widths = [None] * 0x110000
        for char, (width,) in UcdFile(EASTASIAN_WIDTH, version).expanded():
            widths[char] = width

        for i in range(0, 0x110000):
            if table[i] is not None:
                table[i].east_asian_width = widths[i]
        self.widths = widths

        # Read DerivedBidiClass.txt for bidi classes
        # see https://www.unicode.org/reports/tr44/#Missing_Conventions
        bidi_classes = [None] * 0x110000
        for i in range(0, 0x110000):
            if table[i] is not None:
                bidi_classes[i] = table[i].bidi_class
        if version != '3.2.0':
            missing_re = re.compile(
                r'# @missing: ([\dA-F]+\.\.[\dA-F]+); (\w+)'
            )
            with open_data(DERIVED_BIDI_CLASS, version) as f:
                for l in f:
                    m = missing_re.match(l)
                    if not m:
                        continue
                    name = BIDI_LONG_NAMES[m[2]]
                    for i in expand_range(m[1]):
                        bidi_classes[i] = name
            for char, (bidi,) in UcdFile(DERIVED_BIDI_CLASS, version).expanded():
                bidi_classes[char] = bidi
        self.bidi_classes = bidi_classes

        for char, (propname, *propinfo) in UcdFile(DERIVED_CORE_PROPERTIES, version).expanded():
            if not propinfo:
                # binary property
                if table[char]:
                    # Some properties (e.g. Default_Ignorable_Code_Point)
                    # apply to unassigned code points; ignore them
                    table[char].binary_properties.add(propname)
            elif propname == 'InCB':  # Indic_Conjunct_Break
                table[char].incb, = propinfo

        for char_range, value in UcdFile(LINE_BREAK, version):
            if value not in MANDATORY_LINE_BREAKS:
                continue
            for char in expand_range(char_range):
                table[char].binary_properties.add('Line_Break')

        # We only want the quickcheck properties
        # Format: NF?_QC; Y(es)/N(o)/M(aybe)
        # Yes is the default, hence only N and M occur
        # In 3.2.0, the format was different (NF?_NO)
        # The parsing will incorrectly determine these as
        # "yes", however, unicodedata.c will not perform quickchecks
        # for older versions, and no delta records will be created.
        quickchecks = [0] * 0x110000
        qc_order = 'NFD_QC NFKD_QC NFC_QC NFKC_QC'.split()
        for s in UcdFile(DERIVEDNORMALIZATION_PROPS, version):
            if len(s) < 2 or s[1] not in qc_order:
                continue
            quickcheck = 'MN'.index(s[2]) + 1 # Maybe or No
            quickcheck_shift = qc_order.index(s[1])*2
            quickcheck <<= quickcheck_shift
            for char in expand_range(s[0]):
                assert not (quickchecks[char]>>quickcheck_shift)&3
                quickchecks[char] |= quickcheck
        for i in range(0, 0x110000):
            if table[i] is not None:
                table[i].quick_check = quickchecks[i]

        with open_data(UNIHAN, version) as file:
            zip = zipfile.ZipFile(file)
            if version == '3.2.0':
                data = zip.open('Unihan-3.2.0.txt').read()
            else:
                data = zip.open('Unihan_NumericValues.txt').read()
        for line in data.decode("utf-8").splitlines():
            if not line.startswith('U+'):
                continue
            code, tag, value = line.split(None, 3)[:3]
            if tag not in ('kAccountingNumeric', 'kPrimaryNumeric',
                           'kOtherNumeric'):
                continue
            value = value.strip().replace(',', '')
            i = int(code[2:], 16)
            # Patch the numeric field
            if table[i] is not None:
                table[i].numeric_value = value

        sc = self.special_casing = {}
        for data in UcdFile(SPECIAL_CASING, version):
            if data[4]:
                # We ignore all conditionals (since they depend on
                # languages) except for one, which is hardcoded. See
                # handle_capital_sigma in unicodeobject.c.
                continue
            c = int(data[0], 16)
            lower = [int(char, 16) for char in data[1].split()]
            title = [int(char, 16) for char in data[2].split()]
            upper = [int(char, 16) for char in data[3].split()]
            sc[c] = (lower, title, upper)

        cf = self.case_folding = {}
        if version != '3.2.0':
            for data in UcdFile(CASE_FOLDING, version):
                if data[1] in "CF":
                    c = int(data[0], 16)
                    cf[c] = [int(char, 16) for char in data[2].split()]

        if version != "3.2.0":
            grapheme_breaks = [None] * 0x110000
            for char, (prop,) in UcdFile(GRAPHEME_CLUSTER_BREAK, version).expanded():
                grapheme_breaks[char] = prop
            self.grapheme_breaks = grapheme_breaks

            ext_picts = [False] * 0x110000
            for char, (prop,) in UcdFile(EMOJI_DATA, version).expanded():
                if prop == 'Extended_Pictographic':
                    ext_picts[char] = True
            self.ext_picts = ext_picts

            # See https://www.unicode.org/versions/Unicode17.0.0/core-spec/chapter-3/#G64189
            self.blocks = []
            for record in UcdFile(BLOCKS, version).records():
                start_end, name = record
                start, end = [int(c, 16) for c in start_end.split('..')]
                self.blocks.append((start, end, name))
            self.blocks.sort()