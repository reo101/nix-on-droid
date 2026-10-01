from apps import app
from apps.base import DEFAULT_APP_ID
from common import screenshot, wait_for, install_and_launch, BOOTSTRAP_URL


def run(d):
    nod = install_and_launch(d)
    app.answer_bootstrap_prompt(d, BOOTSTRAP_URL)

    wait_for(d, 'Welcome to Nix-on-Droid!')
    screenshot(d, 'bootstrap-begins')
    wait_for(d, 'Do you want to set it up with flakes? (y/N)')
    app.type_line(d, '')
    wait_for(d, 'Setting up Nix-on-Droid with channels...')

    wait_for(d, 'Installing and updating nix-channels...')
    wait_for(d, 'unpacking channels...')
    if app.app_id != DEFAULT_APP_ID:
        wait_for(d, f'Setting build.androidAppId = "{app.app_id}"...', timeout=600)

    wait_for(d, 'Installing first Nix-on-Droid generation...', timeout=600)
    wait_for(d, 'Copying default Nix-on-Droid config...', timeout=180)
    wait_for(d, 'Congratulations!')
    wait_for(d, 'See config file for further information.')
    wait_for(d, 'bash-5.2$')
    screenshot(d, 'bootstrap-ends')

    app.type_line(d, 'echo smoke-test | base64')
    wait_for(d, 'c21va2UtdGVzdAo=')

    screenshot(d, 'success-bootstrap-channels')

    return nod
