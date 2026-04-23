def run_command(client: RAGFlowClient, command_dict: dict):
    command_type = command_dict["type"]

    match command_type:
        case "benchmark":
            run_benchmark(client, command_dict)
        case "login_user":
            client.login_user(command_dict)
        case "ping_server":
            return client.ping_server(command_dict)
        case "register_user":
            client.register_user(command_dict)
        case "list_services":
            client.list_services()
        case "show_service":
            client.show_service(command_dict)
        case "restart_service":
            client.restart_service(command_dict)
        case "shutdown_service":
            client.shutdown_service(command_dict)
        case "startup_service":
            client.startup_service(command_dict)
        case "list_users":
            client.list_users(command_dict)
        case "show_user":
            client.show_user(command_dict)
        case "drop_user":
            client.drop_user(command_dict)
        case "alter_user":
            client.alter_user(command_dict)
        case "create_user":
            client.create_user(command_dict)
        case "activate_user":
            client.activate_user(command_dict)
        case "list_datasets":
            client.handle_list_datasets(command_dict)
        case "list_agents":
            client.handle_list_agents(command_dict)
        case "create_role":
            client.create_role(command_dict)
        case "drop_role":
            client.drop_role(command_dict)
        case "alter_role":
            client.alter_role(command_dict)
        case "list_roles":
            client.list_roles(command_dict)
        case "show_role":
            client.show_role(command_dict)
        case "grant_permission":
            client.grant_permission(command_dict)
        case "revoke_permission":
            client.revoke_permission(command_dict)
        case "alter_user_role":
            client.alter_user_role(command_dict)
        case "show_user_permission":
            client.show_user_permission(command_dict)
        case "show_version":
            client.show_version(command_dict)
        case "grant_admin":
            client.grant_admin(command_dict)
        case "revoke_admin":
            client.revoke_admin(command_dict)
        case "generate_key":
            client.generate_key(command_dict)
        case "list_keys":
            client.list_keys(command_dict)
        case "drop_key":
            client.drop_key(command_dict)
        case "set_variable":
            client.set_variable(command_dict)
        case "show_variable":
            client.show_variable(command_dict)
        case "list_variables":
            client.list_variables(command_dict)
        case "list_configs":
            client.list_configs(command_dict)
        case "list_environments":
            client.list_environments(command_dict)
        case "show_fingerprint":
            client.show_fingerprint(command_dict)
        case "set_license":
            client.set_license(command_dict)
        case "set_license_config":
            client.set_license_config(command_dict)
        case "show_license":
            client.show_license(command_dict)
        case "check_license":
            client.check_license(command_dict)
        case "list_server_configs":
            client.list_server_configs(command_dict)
        case "create_model_provider":
            client.create_model_provider(command_dict)
        case "drop_model_provider":
            client.drop_model_provider(command_dict)
        case "show_current_user":
            client.show_current_user(command_dict)
        case "set_default_model":
            client.set_default_model(command_dict)
        case "reset_default_model":
            client.reset_default_model(command_dict)
        case "list_user_datasets":
            return client.list_user_datasets(command_dict)
        case "create_user_dataset":
            client.create_user_dataset(command_dict)
        case "drop_user_dataset":
            client.drop_user_dataset(command_dict)
        case "list_user_dataset_files":
            return client.list_user_dataset_files(command_dict)
        case "list_user_dataset_documents":
            return client.list_user_dataset_documents(command_dict)
        case "list_user_datasets_metadata":
            return client.list_user_datasets_metadata(command_dict)
        case "list_user_documents_metadata_summary":
            return client.list_user_documents_metadata_summary(command_dict)
        case "list_user_agents":
            return client.list_user_agents(command_dict)
        case "list_user_chats":
            return client.list_user_chats(command_dict)
        case "create_user_chat":
            client.create_user_chat(command_dict)
        case "drop_user_chat":
            client.drop_user_chat(command_dict)
        case "create_dataset_table":
            client.create_dataset_table(command_dict)
        case "drop_dataset_table":
            client.drop_dataset_table(command_dict)
        case "create_metadata_table":
            client.create_metadata_table(command_dict)
        case "drop_metadata_table":
            client.drop_metadata_table(command_dict)
        case "create_chat_session":
            client.create_chat_session(command_dict)
        case "drop_chat_session":
            client.drop_chat_session(command_dict)
        case "list_chat_sessions":
            return client.list_chat_sessions(command_dict)
        case "chat_on_session":
            client.chat_on_session(command_dict)
        case "list_user_model_providers":
            client.list_user_model_providers(command_dict)
        case "list_user_default_models":
            client.list_user_default_models(command_dict)
        case "parse_dataset_docs":
            client.parse_dataset_docs(command_dict)
        case "parse_dataset":
            client.parse_dataset(command_dict)
        case "import_docs_into_dataset":
            client.import_docs_into_dataset(command_dict)
        case "search_on_datasets":
            return client.search_on_datasets(command_dict)
        case "get_chunk":
            return client.get_chunk(command_dict)
        case "insert_dataset_from_file":
            return client.insert_dataset_from_file(command_dict)
        case "insert_metadata_from_file":
            return client.insert_metadata_from_file(command_dict)
        case "update_chunk":
            return client.update_chunk(command_dict)
        case "set_metadata":
            return client.set_metadata(command_dict)
        case "remove_tags":
            return client.remove_tags(command_dict)
        case "remove_chunks":
            return client.remove_chunks(command_dict)
        case "list_chunks":
            return client.list_chunks(command_dict)
        case "meta":
            _handle_meta_command(command_dict)
        case _:
            print(f"Command '{command_type}' would be executed with API")