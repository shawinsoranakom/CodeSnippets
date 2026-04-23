def download_run(args):
    """Download a run."""

    output_dir = '%s' % args.run

    if not args.test and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    if args.run_metadata:
        run_url = 'https://dev.azure.com/ansible/ansible/_apis/pipelines/%s/runs/%s?api-version=6.0-preview.1' % (args.pipeline_id, args.run)
        with urllib.request.urlopen(run_url) as run_info_response:
            run = json.load(run_info_response)

        path = os.path.join(output_dir, 'run.json')
        contents = json.dumps(run, sort_keys=True, indent=4)

        if args.verbose:
            print(path)

        if not args.test:
            with open(path, 'w') as metadata_fd:
                metadata_fd.write(contents)

    with urllib.request.urlopen('https://dev.azure.com/ansible/ansible/_apis/build/builds/%s/timeline?api-version=6.0' % args.run) as timeline_response:
        timeline = json.load(timeline_response)
    roots = set()
    by_id = {}
    children_of = {}
    parent_of = {}
    for r in timeline['records']:
        thisId = r['id']
        parentId = r['parentId']

        by_id[thisId] = r

        if parentId is None:
            roots.add(thisId)
        else:
            parent_of[thisId] = parentId
            children_of[parentId] = children_of.get(parentId, []) + [thisId]

    allowed = set()

    def allow_recursive(ei):
        allowed.add(ei)
        for ci in children_of.get(ei, []):
            allow_recursive(ci)

    for ri in roots:
        r = by_id[ri]
        allowed.add(ri)
        for ci in children_of.get(r['id'], []):
            c = by_id[ci]
            if not args.match_job_name.match("%s %s" % (r['name'], c['name'])):
                continue
            allow_recursive(c['id'])

    if args.artifacts:
        artifact_list_url = 'https://dev.azure.com/ansible/ansible/_apis/build/builds/%s/artifacts?api-version=6.0' % args.run
        with urllib.request.urlopen(artifact_list_url) as artifact_list_response:
            artifact_list = json.load(artifact_list_response)

        for artifact in artifact_list['value']:
            if artifact['source'] not in allowed or not args.match_artifact_name.match(artifact['name']):
                continue
            if args.verbose:
                print('%s/%s' % (output_dir, artifact['name']))
            if not args.test:
                with urllib.request.urlopen(artifact['resource']['downloadUrl']) as response:
                    with io.BytesIO() as buffer:
                        shutil.copyfileobj(response, buffer)
                        buffer.seek(0)
                        with zipfile.ZipFile(buffer) as archive:
                            archive.extractall(path=output_dir)

    if args.console_logs:
        for r in timeline['records']:
            if not r['log'] or r['id'] not in allowed or not args.match_artifact_name.match(r['name']):
                continue
            names = []
            parent_id = r['id']
            while parent_id is not None:
                p = by_id[parent_id]
                name = p['name']
                if name not in names:
                    names = [name] + names
                parent_id = parent_of.get(p['id'], None)

            path = " ".join(names)

            # Some job names have the separator in them.
            path = path.replace(os.sep, '_')

            log_path = os.path.join(output_dir, '%s.log' % path)
            if args.verbose:
                print(log_path)
            if not args.test:
                with urllib.request.urlopen(r['log']['url']) as log:
                    with open(log_path, 'wb') as log_file:
                        shutil.copyfileobj(log, log_file)