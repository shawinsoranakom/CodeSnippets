def load_configurations(config_path: str) -> list[BaseConfig]:
    raw_configs = read_config(config_path)
    configurations = []
    ragflow_count = 0
    id_count = 0
    for k, v in raw_configs.items():
        match k:
            case "ragflow":
                name: str = f'ragflow_{ragflow_count}'
                host: str = v['host']
                http_port: int = v['http_port']
                config = RAGFlowServerConfig(id=id_count, name=name, host=host, port=http_port,
                                             service_type="ragflow_server",
                                             detail_func_name="check_ragflow_server_alive")
                configurations.append(config)
                id_count += 1
            case "es":
                name: str = 'elasticsearch'
                url = v['hosts']
                parsed = urlparse(url)
                host: str = parsed.hostname
                port: int = parsed.port
                username: str = v.get('username')
                password: str = v.get('password')
                config = ElasticsearchConfig(id=id_count, name=name, host=host, port=port, service_type="retrieval",
                                             retrieval_type="elasticsearch",
                                             username=username, password=password,
                                             detail_func_name="get_es_cluster_stats")
                configurations.append(config)
                id_count += 1

            case "infinity":
                name: str = 'infinity'
                url = v['uri']
                parts = url.split(':', 1)
                host = parts[0]
                port = int(parts[1])
                database: str = v.get('db_name', 'default_db')
                config = InfinityConfig(id=id_count, name=name, host=host, port=port, service_type="retrieval",
                                        retrieval_type="infinity",
                                        db_name=database, detail_func_name="get_infinity_status")
                configurations.append(config)
                id_count += 1
            case "minio_0":
                name: str = 'minio_0'
                url = v['host']
                parts = url.split(':', 1)
                host = parts[0]
                port = int(parts[1])
                user = v.get('user')
                password = v.get('password')
                config = MinioConfig(id=id_count, name=name, host=host, port=port, user=user, password=password,
                                     service_type="file_store",
                                     store_type="minio", detail_func_name="check_minio_alive")
                configurations.append(config)
                id_count += 1
            case "minio":
                name: str = 'minio'
                url = v['host']
                parts = url.split(':', 1)
                host = parts[0]
                port = int(parts[1])
                user = v.get('user')
                password = v.get('password')
                config = MinioConfig(id=id_count, name=name, host=host, port=port, user=user, password=password,
                                     service_type="file_store",
                                     store_type="minio", detail_func_name="check_minio_alive")
                configurations.append(config)
                id_count += 1
            case "redis":
                name: str = 'redis'
                url = v['host']
                parts = url.split(':', 1)
                host = parts[0]
                port = int(parts[1])
                password = v.get('password')
                db: int = v.get('db')
                config = RedisConfig(id=id_count, name=name, host=host, port=port, password=password, database=db,
                                     service_type="message_queue", mq_type="redis", detail_func_name="get_redis_info")
                configurations.append(config)
                id_count += 1
            case "mysql":
                name: str = 'mysql'
                host: str = v.get('host')
                port: int = v.get('port')
                username = v.get('user')
                password = v.get('password')
                config = MySQLConfig(id=id_count, name=name, host=host, port=port, username=username, password=password,
                                     service_type="meta_data", meta_type="mysql", detail_func_name="get_mysql_status")
                configurations.append(config)
                id_count += 1
            case "admin":
                pass
            case "task_executor":
                name: str = 'task_executor'
                host: str = v.get('host', '')
                port: int = v.get('port', 0)
                message_queue_type: str = v.get('message_queue_type')
                config = TaskExecutorConfig(id=id_count, name=name, host=host, port=port, message_queue_type=message_queue_type,
                                            service_type="task_executor", detail_func_name="check_task_executor_alive")
                configurations.append(config)
                id_count += 1
            case "rabbitmq":
                name: str = 'rabbitmq'
                host: str = v.get('host')
                port: int = v.get('port')
                config = RabbitMQConfig(id=id_count, name=name, host=host, port=port,
                                        service_type="message_queue", mq_type="rabbitmq", detail_func_name="check_rabbitmq_alive")
                configurations.append(config)
                id_count += 1
            case _:
                logging.warning(f"Unknown configuration key: {k}")
                continue

    return configurations