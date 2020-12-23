import random
import re
import subprocess


__all__ = ['WindscribeException', 'WindscribeVpn']


class WindscribeException(Exception):
    pass


class WindscribeVpn:
    VALID_REGION = ['US', 'CA', 'UK', 'HK', 'DE', 'FR', 'NL', 'CH', 'NO', 'RO']

    def __init__(self, nr_try_login=5, nr_try_logout=5, nr_try_change_vpn=5, nr_relogin=5):
        self.nr_try_change_vpn = nr_try_change_vpn
        self.nr_relogin = nr_relogin
        self.nr_try_login = nr_try_login
        self.nr_try_logout = nr_try_logout

    def login_windscribe(self):
        for t in range(self.nr_try_login):
            if self._login_windscribe_1():
                return True
        raise WindscribeException(f'Cannot login in {self.nr_try_login} times')

    def logout_windscribe(self):
        shell = subprocess.run(['windscribe', 'logout'], capture_output=True)
        for t in range(self.nr_try_logout):
            if 'Logged Out' in shell.stdout.decode('utf-8'):
                return True
        raise WindscribeException(f'Cannot logout in {self.nr_try_logout} times')

    def change_vpn_via_windscribe(self):
        if self._change_vpn_via_windscribe_1('best'):
            return True
        for t1 in range(self.nr_relogin):
            for t2 in range(self.nr_try_change_vpn):
                region = self.VALID_REGION[random.randint(0, len(self.VALID_REGION) - 1)]
                if self._change_vpn_via_windscribe_1(region):
                    return True
            self.logout_windscribe()
            self.login_windscribe()

        raise WindscribeException(f'Cannot change vpn in {self.nr_try_change_vpn}x{self.nr_relogin} times')

    @staticmethod
    def _change_vpn_via_windscribe_1(region):
        shell = subprocess.run(['windscribe', 'connect', region], capture_output=True)
        checked_stdout = shell.stdout.decode('utf-8')
        print(checked_stdout)
        if re.match('Your IP changed from .* to Unknown', checked_stdout) is not None:
            return False
        if 'Connected to' in checked_stdout and 'Your IP changed from' in checked_stdout:
            return True
        else:
            return False

    @staticmethod
    def _login_windscribe_1():
        shell = subprocess.run(['expect', '/windscribe_login'], capture_output=True)
        checked_stdout = '\n'.join(shell.stdout.decode('utf-8').split('\n')[1:])
        if 'API Error' in checked_stdout:
            print('Windscribe login failed')
            return False
        elif 'Already Logged in' in checked_stdout:
            print('Windscribe already logged in')
            return True
        elif 'Logged in' in checked_stdout:
            print('Windscribe login success')
            return True
        else:
            print('Windscribe Unknown Error')
            return False
