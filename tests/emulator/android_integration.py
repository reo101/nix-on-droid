import base64
import time

import bootstrap_channels
from apps import app

from common import screenshot, wait_for


def run(d):
    OPENERS = ['termux-open', 'termux-open-url', 'xdg-open']
    TOOLS = ['am', 'termux-setup-storage', 'termux-reload-settings',
             'termux-wake-lock', 'termux-wake-unlock'] + OPENERS

    nod = bootstrap_channels.run(d)

    # Verify that android-integration tools aren't installed by default
    for toolname in TOOLS:
        app.type_line(d, toolname)
        wait_for(d, f'bash: {toolname}: command not found')
        screenshot(d, f'no-{toolname}')

    # Apply a config that enables android-integration tools
    cfg = ('/data/local/tmp/n-o-d/unpacked/tests/on-device/'
           'config-android-integration.nix')
    app.type_line(d, f'cp {cfg} .config/nixpkgs/nix-on-droid.nix')
    screenshot(d, 'pre-switch')
    app.type_line(d, 'nix-on-droid switch && echo integration  tools  installed')
    wait_for(d, 'integration tools installed')
    screenshot(d, 'post-switch')

    # Verify am is there
    app.type_line(d, 'am | head -n2')
    wait_for(d, 'termux-am is a wrapper script')
    screenshot(d, 'am-appears')

    # Some apps only implement the requests used by the integration tools.
    if app.capabilities.restricted_am:
        print('Skipping full am and overlay permission checks: '
              'the app only handles integration-tool requests.')
        app.type_line(d, 'am start -a android.settings.SETTINGS 2>&1 | head -n5')
        screenshot(d, 'am-invoked')
        wait_for(d, app.restricted_am_message)
        screenshot(d, 'am-refused')
    else:
        if app.capabilities.overlay_permission:
            # Smoke-test that am doesn't work before granting permission.
            app.type_line(d, 'am start -a android.settings.SETTINGS 2>&1 | head -n5')
            screenshot(d, 'am-invoked for the first time')
            app.wait_for_overlay_permission(d)
            nod.permissions += 'android.permission.SYSTEM_ALERT_WINDOW'
        else:
            print('Skipping overlay permission check: the app does not require it.')

        # Smoke-test that am works.
        app.type_line(d, 'am start -a android.settings.SETTINGS')
        screenshot(d, 'settings-opening')
        wait_for(d, 'Search settings')
        wait_for(d, 'Network')
        screenshot(d, 'settings-awaited')
        d.ui.press('back')
        screenshot(d, 'back-from-settings')

    # Verify we're back
    app.type_line(d, 'am | head -n2')
    wait_for(d, 'termux-am is a wrapper script')

    # Verify termux-setup-storage is there
    app.type_line(d, 'termux-setup-storage')
    screenshot(d, 'termux-setup-storage-invoked')
    if app.capabilities.initial_storage_prompt:
        app.answer_storage_prompt(d)
    else:
        print('Skipping initial storage permission prompt: the app does not show one.')

    app.type_line(d, 'ls -l storage')
    screenshot(d, 'storage-listed')
    wait_for(d, 'pictures -> /storage/emulated/0/Pictures')
    wait_for(d, 'shared -> /storage/emulated/0')
    screenshot(d, 'storage-listed-ok')

    # Invoke termux-setup-storage again
    app.type_line(d, 'termux-setup-storage')
    screenshot(d, 'termux-setup-storage-invoked-again')
    wait_for(d, 'already exists')
    wait_for(d, 'Do you want to continue?')
    app.type_line(d, '')
    wait_for(d, 'Aborting configuration and leaving')

    # Verify that *-open* commands work
    for opener in OPENERS:
        app.type_line(d, f'{opener} https://nix-on-droid.unboiled.info/README.txt')
        screenshot(d, f'{opener}-opened')
        wait_for(d, 'This is Nix-on-Droid.')
        screenshot(d, f'{opener}-waited')
        d.ui.press('back')
        screenshot(d, f'{opener}-back')
        wait_for(d, f'{opener} https://nix-on-droid.unboiled.info/README.txt')

    # test termux-wake-lock/termux-wake-unlock
    app.check_wake_lock(d, False, initial=True)

    app.type_line(d, 'termux-wake-lock')
    time.sleep(3)
    screenshot(d, 'wake-lock-command')
    app.check_wake_lock(d, True)

    app.type_line(d, 'termux-wake-unlock')
    if not app.capabilities.notifications:
        time.sleep(3)
    screenshot(d, 'wake-unlock-command')
    app.check_wake_lock(d, False)

    # Test termux-reload-settings
    assert 'PGUP' in app.extra_keys(d)
    assert 'F12' not in app.extra_keys(d)

    app.type_line(d, 'mkdir ~/.termux')
    cmd = 'echo "extra-keys=[[\'F12\']]" > ~/.termux/termux.properties'
    cmd_base64 = base64.b64encode(cmd.encode()).decode()
    app.type_line(d, f'echo {cmd_base64} | base64 -d | bash -s')
    screenshot(d, 'pre-reload')
    app.type_line(d, 'termux-reload-settings')
    time.sleep(1)
    screenshot(d, 'post-reload')
    assert 'PGUP' not in app.extra_keys(d)
    assert 'F12' in app.extra_keys(d)

    app.type_line(d, 'rm -r ~/.termux')
    screenshot(d, 'pre-reload-back')
    app.type_line(d, 'termux-reload-settings')
    time.sleep(1)
    screenshot(d, 'post-reload-back')
    assert 'PGUP' in app.extra_keys(d)
    assert 'F12' not in app.extra_keys(d)
