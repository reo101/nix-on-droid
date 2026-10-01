import bootstrap_channels
import subprocess
import sys

from apps import app
from common import screenshot, wait_for

STD = f'{app.files_dir}/home/.cache/nix-on-droid-self-test'


def run(d):
    bootstrap_channels.run(d)

    # re-login for variety. the other on-device-test (uiautomator one) does not
    app.type_line(d, 'exit', enter=False)
    screenshot(d, 'pre-relogin')
    d.ui.press('enter')

    app.launch(d)
    d.ui.press('enter')
    screenshot(d, 'post-relogin')
    wait_for(d, 'bash-5.2$')

    # run tests in a way that'd display progress in CI
    user = d.su(f'stat -c %U /data/data/{app.app_id}').output.strip()
    # WARNING: assumes `su 0` style `su` that doesn't support -c from now on
    print(f'{user=}')
    sys.stdout.flush()
    sys.stderr.flush()
    for cmd in [
        'id',
        f'mkdir -p {STD}',
        f'touch {STD}/confirmation-granted',
        f'{app.files_dir}/usr/bin/login echo test',
        f'{app.files_dir}/usr/bin/login id',
        (f'cd {app.files_dir}/home; '
         'pwd; '
         'id; '
         f'env PATH= {app.files_dir}/usr/bin/login '
         ' nix-on-droid on-device-test'),
    ]:
        print(f'running {cmd} as {user} with capture:')
        p = subprocess.Popen(['adb', 'shell', 'su', '0', 'su', user,
                              'sh', '-c', f"'{cmd}'"],
                             encoding='utf-8',
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT)
        out = ''
        while p.poll() is None:
            line = p.stdout.readline()
            out += line
            sys.stdout.write('> ' + line)
            sys.stdout.flush()
        print(f'returncode: {p.returncode}')
        # guess what, it can swallow the exit code!

    assert 'tests, 0 failures in' in out  # of the last command
