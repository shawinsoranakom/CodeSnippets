def fix_kv(self, k, v):
    # append type to names to preserve legacy naming in logs
    # avoids overlapping key namespaces with different types
    # e.g. log.info() creates 'msg' -> 'msg$s'
    #      log.event() creates 'msg.health.logMonoTime' -> 'msg.health.logMonoTime$i'
    #      because overlapping namespace 'msg' caused problems
    if isinstance(v, (str, bytes)):
      k += "$s"
    elif isinstance(v, float):
      k += "$f"
    elif isinstance(v, bool):
      k += "$b"
    elif isinstance(v, int):
      k += "$i"
    elif isinstance(v, dict):
      nv = {}
      for ik, iv in v.items():
        ik, iv = self.fix_kv(ik, iv)
        nv[ik] = iv
      v = nv
    elif isinstance(v, list):
      k += "$a"
    return k, v