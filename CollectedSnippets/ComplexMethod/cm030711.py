def run_grapheme_break_tests(self, testdata):
        for line in testdata:
            line, _, comment = line.partition('#')
            line = line.strip()
            if not line:
                continue
            comment = comment.strip()

            chunks = []
            breaks = []
            pos = 0
            for field in line.replace('×', ' ').split():
                if field == '÷':
                    chunks.append('')
                    breaks.append(pos)
                else:
                    chunks[-1] += chr(int(field, 16))
                    pos += 1
            self.assertEqual(chunks.pop(), '', line)
            input = ''.join(chunks)
            with self.subTest(line):
                result = list(unicodedata.iter_graphemes(input))
                self.assertEqual(list(map(str, result)), chunks, comment)
                self.assertEqual([x.start for x in result], breaks[:-1], comment)
                self.assertEqual([x.end for x in result], breaks[1:], comment)
                for i in range(1, len(breaks) - 1):
                    result = list(unicodedata.iter_graphemes(input, breaks[i]))
                    self.assertEqual(list(map(str, result)), chunks[i:], comment)
                    self.assertEqual([x.start for x in result], breaks[i:-1], comment)
                    self.assertEqual([x.end for x in result], breaks[i+1:], comment)