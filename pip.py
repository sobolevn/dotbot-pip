import os
import subprocess

import dotbot


class Brew(dotbot.Plugin):
    _pipsi_directive = 'pipsi'
    _default_binary = 'pip'

    _supported_directives = [
        'pip',  # it is not the same as default binary.
        _pipsi_directive,
    ]

    # API methods

    def can_handle(self, directive):
        return directive in self._supported_directives

    def handle(self, directive, data):
        data = self._maybe_convert_to_dict(data)

        try:
            self._do_requirements_exist(data)
            self._handle_install(directive, data)
            return True
        except ValueError as e:
            self._log.error(e)
            return False

    # Utility

    @property
    def cwd(self):
        return self._context.base_directory()

    # Inner logic

    def _maybe_convert_to_dict(self, data):
        if isinstance(data, str):
            return {'file': data}
        return data

    def _do_requirements_exist(self, data):
        message = 'Requirements file does not exist.'
        filename = data.get('file')
        if not filename:
            raise ValueError(message)

        path = os.path.join(self.cwd, filename)
        if not os.path.isfile(path):
            raise ValueError(message)

    def _get_binary(self, directive, data):
        """
        Return correct binary path.

        Respects `binary` key for `pip`.
        Returns just `pipsi` for `pipsi`.
        """
        if directive == self._pipsi_directive:
            return self._pipsi_directive

        return data.get('binary', self._default_binary)

    def _prepare_requirements(self, directive, data):
        """
        A tricky part. Resolving dependencies.

        `pipsi` does not support `requirements.txt` files.
        So we need to read all the requirements one by one and install
        them separately.

        And just return the file path with `-r` for `pip`.
        """
        if directive == self._pipsi_directive:
            with open(os.path.join(self.cwd, data['file'])) as r:
                requirements = r.readlines()

            requirements = filter(
                lambda x: x != '\n' and not x.startswith('#'),
                requirements
            )
            return requirements

        # Just `pip`:
        return [
            '-r {}'.format(data['file']),
        ]


    # Handlers

    def _handle_install(self, directive, data):
        binary = self._get_binary(directive, data)
        requirements = self._prepare_requirements(directive, data)
        param = ''
        if directive != self._pipsi_directive:
            param = '--user'

        for req in requirements:
            command = '{} install {} {}'.format(binary, param, req)

            with open(os.devnull, 'w') as devnull:
                result = subprocess.call(
                    command,
                    shell=True,
                    stdin=devnull,
                    stdout=devnull,
                    stderr=devnull,
                    cwd=self.cwd,
                )

                if result not in [0, 1]:
                    raise ValueError('Failed to install requirements.')

