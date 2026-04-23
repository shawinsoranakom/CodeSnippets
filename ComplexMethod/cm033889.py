def run(self, terms, variables=None, **kwargs):

        self.set_options(var_options=variables, direct=kwargs)

        ret = []
        for term in terms:
            display.vvvv("url lookup connecting to %s" % term)
            try:
                response = open_url(
                    term, validate_certs=self.get_option('validate_certs'),
                    use_proxy=self.get_option('use_proxy'),
                    url_username=self.get_option('username'),
                    url_password=self.get_option('password'),
                    headers=self.get_option('headers'),
                    force=self.get_option('force'),
                    timeout=self.get_option('timeout'),
                    http_agent=self.get_option('http_agent'),
                    force_basic_auth=self.get_option('force_basic_auth'),
                    follow_redirects=self.get_option('follow_redirects'),
                    use_gssapi=self.get_option('use_gssapi'),
                    unix_socket=self.get_option('unix_socket'),
                    ca_path=self.get_option('ca_path'),
                    unredirected_headers=self.get_option('unredirected_headers'),
                    ciphers=self.get_option('ciphers'),
                    use_netrc=self.get_option('use_netrc')
                )
            except HTTPError as e:
                raise AnsibleError("Received HTTP error for %s : %s" % (term, to_native(e)))
            except URLError as e:
                raise AnsibleError("Failed lookup url for %s : %s" % (term, to_native(e)))
            except SSLValidationError as e:
                raise AnsibleError("Error validating the server's certificate for %s: %s" % (term, to_native(e)))
            except ConnectionError as e:
                raise AnsibleError("Error connecting to %s: %s" % (term, to_native(e)))

            if self.get_option('split_lines'):
                for line in response.read().splitlines():
                    ret.append(to_text(line))
            else:
                ret.append(to_text(response.read()))
        return ret