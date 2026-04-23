def convert_yaml_to_env(yaml_file, target_parameters, output_env_file, prefix):
    """Converts a YAML file into .env file format for specified target parameters under 'stringData' and 'data'.

    :param yaml_file: Path to the YAML file.
    :param target_parameters: List of keys to extract from the YAML file.
    :param output_env_file: Path to the output .env file.
    :param prefix: Prefix for environment variables.
    """
    try:
        # Load the YAML file
        with open(yaml_file, 'r') as file:
            yaml_data = yaml.safe_load(file)

        # Extract sections
        string_data = yaml_data.get('stringData', None)
        data = yaml_data.get('data', None)

        if string_data:
            env_source = string_data
            process_base64 = False
        elif data:
            env_source = data
            process_base64 = True
        else:
            print(
                "Error: Neither 'stringData' nor 'data' section found in the YAML file."
            )
            return

        env_lines = []

        for param in target_parameters:
            if param in env_source:
                value = env_source[param]
                if process_base64:
                    try:
                        decoded_value = base64.b64decode(value).decode('utf-8')
                        formatted_value = (
                            decoded_value.replace('\n', '\\n')
                            if '\n' in decoded_value
                            else decoded_value
                        )
                    except Exception as decode_error:
                        print(f"Error decoding base64 for '{param}': {decode_error}")
                        continue
                else:
                    formatted_value = (
                        value.replace('\n', '\\n')
                        if isinstance(value, str) and '\n' in value
                        else value
                    )

                new_key = prefix + param.upper().replace('-', '_')
                env_lines.append(f'{new_key}={formatted_value}')
            else:
                print(
                    f"Warning: Parameter '{param}' not found in the selected section."
                )

        # Write to the .env file
        with open(output_env_file, 'a') as env_file:
            env_file.write('\n'.join(env_lines) + '\n')

    except Exception as e:
        print(f'Error: {e}')