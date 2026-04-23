def load_route_metadata(route):
  from openpilot.common.params import Params, UnknownKeyName
  path = next((item for item in route.log_paths() if item), None)
  if not path:
    raise Exception('error getting route metadata: cannot find any uploaded logs')
  lr = LogReader(path)
  init_data, car_params = lr.first('initData'), lr.first('carParams')

  params = Params()
  for entry in init_data.params.entries:
    try:
      params.put(entry.key, params.cpp2python(entry.key, entry.value))
    except UnknownKeyName:
      pass

  origin = init_data.gitRemote.split('/')[3] if len(init_data.gitRemote.split('/')) > 3 else 'unknown'
  return {
    'version': init_data.version, 'route': route.name.canonical_name,
    'car': car_params.carFingerprint if car_params else 'unknown', 'origin': origin,
    'branch': init_data.gitBranch, 'commit': init_data.gitCommit[:7], 'modified': str(init_data.dirty).lower(),
  }