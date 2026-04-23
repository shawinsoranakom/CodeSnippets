def try_load_resource_provider(resource_type: str) -> ResourceProvider | None:
        # TODO: unify namespace of plugins
        if resource_type and resource_type.startswith("Custom"):
            resource_type = "AWS::CloudFormation::CustomResource"

        # 1. try to load pro resource provider
        # prioritise pro resource providers
        if PRO_RESOURCE_PROVIDERS:
            try:
                plugin = pro_plugin_manager.load(resource_type)
                return plugin.factory()
            except ValueError:
                # could not find a plugin for that name
                pass
            except Exception:
                LOG.warning(
                    "Failed to load PRO resource type %s as a ResourceProvider.",
                    resource_type,
                    exc_info=LOG.isEnabledFor(logging.DEBUG) and config.CFN_VERBOSE_ERRORS,
                )

        # 2. try to load community resource provider
        try:
            plugin = plugin_manager.load(resource_type)
            return plugin.factory()
        except ValueError:
            # could not find a plugin for that name
            pass
        except Exception:
            if config.CFN_VERBOSE_ERRORS:
                LOG.warning(
                    "Failed to load community resource type %s as a ResourceProvider.",
                    resource_type,
                    exc_info=LOG.isEnabledFor(logging.DEBUG) and config.CFN_VERBOSE_ERRORS,
                )

        # we could not find the resource provider
        return None