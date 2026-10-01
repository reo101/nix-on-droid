from apps import app
from common import screenshot, wait_for


def run(d):
    wait_for(d, 'bash-5.2$')

    app.type_line(d, 'nix-on-droid on-device-test')
    wait_for(d, 'These semi-automated tests are destructive', timeout=180)
    wait_for(d, 'Proceeding will wreck your installation.')
    wait_for(d, 'Do you still wish to proceed?')
    app.type_line(d, 'I do')
    screenshot(d, 'tests-started')

    if app.capabilities.notifications:
        app.acquire_wake_lock_for_tests(d)

    app.allow_permission(d)
    screenshot(d, 'tests-running')

    wait_for(d, 'tests, 0 failures in', timeout=1200)
    screenshot(d, 'tests-finished')
