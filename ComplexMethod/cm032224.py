def process_received(received: DockerServiceApiComModel, save_file_dir="./daas_output", output_manifest=None):
    # Process the received data
    if received.server_message:
        try:
            output_manifest['server_message'] += received.server_message
        except:
            output_manifest['server_message'] = received.server_message
    if received.server_std_err:
        output_manifest['server_std_err'] += received.server_std_err
    if received.server_std_out:
        output_manifest['server_std_out'] += received.server_std_out
    if received.server_file_attach:
        # print(f"Recv file attach: {received.server_file_attach}")
        for file_name, file_content in received.server_file_attach.items():
            new_fp = os.path.join(save_file_dir, file_name)
            new_fp_dir = os.path.dirname(new_fp)
            if not os.path.exists(new_fp_dir):
                os.makedirs(new_fp_dir, exist_ok=True)
            with open(new_fp, 'wb') as f:
                f.write(file_content)
            output_manifest['server_file_attach'].append(new_fp)
    return output_manifest