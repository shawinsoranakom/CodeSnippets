def output(cmd):
    return "docker: '{}' is not a docker command.\n" \
           "See 'docker --help'.".format(cmd)