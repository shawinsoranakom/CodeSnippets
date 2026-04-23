def get_jobs_to_run():
    # The file `pr_files.txt` contains the information about the files changed in a pull request, and it is prepared by
    # the caller (using GitHub api).
    # We can also use the following api to get the information if we don't have them before calling this script.
    # url = f"https://api.github.com/repos/huggingface/transformers/pulls/PULL_NUMBER/files?ref={pr_sha}"
    with open("pr_files.txt") as fp:
        pr_files = json.load(fp)
        pr_files = [{k: v for k, v in item.items() if k in ["filename", "status"]} for item in pr_files]
    pr_files = [item["filename"] for item in pr_files if item["status"] in ["added", "modified"]]

    # models or quantizers
    re_1 = re.compile(r"src/transformers/(models/.*)/modeling_.*\.py")
    re_2 = re.compile(r"src/transformers/(quantizers/quantizer_.*)\.py")

    # tests for models or quantizers
    re_3 = re.compile(r"tests/(models/.*)/test_.*\.py")
    re_4 = re.compile(r"tests/(quantization/.*)/test_.*\.py")

    # files in a model directory but not necessary a modeling file
    re_5 = re.compile(r"src/transformers/(models/.*)/.*\.py")

    regexes = [re_1, re_2, re_3, re_4, re_5]

    jobs_to_run = []
    for pr_file in pr_files:
        for regex in regexes:
            matched = regex.findall(pr_file)
            if len(matched) > 0:
                item = matched[0]
                item = item.replace("quantizers/quantizer_", "quantization/")
                # TODO: for files in `quantizers`, the processed item above may not exist. Try using a fuzzy matching
                if item in repo_content:
                    jobs_to_run.append(item)
                break
    jobs_to_run = sorted(set(jobs_to_run))

    return jobs_to_run