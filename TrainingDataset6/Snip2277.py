def app_alias(self, alias_name):
        return 'function ' + alias_name + ' {\n' \
               '    $history = (Get-History -Count 1).CommandLine;\n' \
               '    if (-not [string]::IsNullOrWhiteSpace($history)) {\n' \
               '        $fuck = $(thefuck $args $history);\n' \
               '        if (-not [string]::IsNullOrWhiteSpace($fuck)) {\n' \
               '            if ($fuck.StartsWith("echo")) { $fuck = $fuck.Substring(5); }\n' \
               '            else { iex "$fuck"; }\n' \
               '        }\n' \
               '    }\n' \
               '    [Console]::ResetColor() \n' \
               '}\n'