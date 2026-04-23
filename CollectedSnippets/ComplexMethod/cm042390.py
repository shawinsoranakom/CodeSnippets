def parse_struct(ss):
  st = "<"
  nams = []
  for l in ss.strip().split("\n"):
    if len(l.strip()) == 0:
      continue
    typ, nam = l.split(";")[0].split()
    #print(typ, nam)
    if typ == "float" or '_Flt' in nam:
      st += "f"
    elif typ == "double" or '_Dbl' in nam:
      st += "d"
    elif typ in ["uint8", "uint8_t"]:
      st += "B"
    elif typ in ["int8", "int8_t"]:
      st += "b"
    elif typ in ["uint32", "uint32_t"]:
      st += "I"
    elif typ in ["int32", "int32_t"]:
      st += "i"
    elif typ in ["uint16", "uint16_t"]:
      st += "H"
    elif typ in ["int16", "int16_t"]:
      st += "h"
    elif typ in ["uint64", "uint64_t"]:
      st += "Q"
    else:
      raise RuntimeError(f"unknown type {typ}")
    if '[' in nam:
      cnt = int(nam.split("[")[1].split("]")[0])
      st += st[-1]*(cnt-1)
      for i in range(cnt):
        nams.append(f'{nam.split("[")[0]}[{i}]')
    else:
      nams.append(nam)
  return st, nams