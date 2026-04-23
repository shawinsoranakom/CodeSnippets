def parse_role_req(requirement):
            if "include" not in requirement:
                role = RoleRequirement.role_yaml_parse(requirement)
                display.vvv("found role %s in yaml file" % to_text(role))
                if "name" not in role and "src" not in role:
                    raise AnsibleError("Must specify name or src for role")
                return [GalaxyRole(self.galaxy, self.lazy_role_api, **role)]
            else:
                b_include_path = to_bytes(requirement["include"], errors="surrogate_or_strict")
                if not os.path.isfile(b_include_path):
                    raise AnsibleError("Failed to find include requirements file '%s' in '%s'"
                                       % (to_native(b_include_path), to_native(requirements_file)))

                with open(b_include_path, 'rb') as f_include:
                    try:
                        return [GalaxyRole(self.galaxy, self.lazy_role_api, **r) for r in
                                (RoleRequirement.role_yaml_parse(i) for i in yaml_load(f_include))]
                    except Exception as e:
                        raise AnsibleError("Unable to load data from include requirements file: %s %s"
                                           % (to_native(requirements_file), to_native(e)))