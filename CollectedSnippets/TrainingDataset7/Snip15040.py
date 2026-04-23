def do_checksum(checksum_algo, release_file):
    with open(os.path.join(dist_path, release_file), "rb") as f:
        return checksum_algo(f.read()).hexdigest()