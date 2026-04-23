def _parse_cmudict(file):
  cmudict = {}
  for line in file:
    if len(line) and (line[0] >= "A" and line[0] <= "Z" or line[0] == "'"):
      parts = line.split("  ")
      word = re.sub(_alt_re, "", parts[0])
      pronunciation = _get_pronunciation(parts[1])
      if pronunciation:
        if word in cmudict:
          cmudict[word].append(pronunciation)
        else:
          cmudict[word] = [pronunciation]
  return cmudict