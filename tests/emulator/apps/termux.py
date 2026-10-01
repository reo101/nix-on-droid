import html
import re
import time

from .base import AppDriver, Capabilities, DEFAULT_APP_ID


class Driver(AppDriver):
    app_id = DEFAULT_APP_ID
    # Use F-Droid through fdroidctl once F-Droid has x86_64 builds.
    apk = 'https://nix-on-droid.unboiled.info/com.termux.nix_188035-x86_64.apk'
    capabilities = Capabilities(
        notifications=True,
        overlay_permission=True,
        restricted_am=False,
        initial_storage_prompt=True,
    )

    def answer_bootstrap_prompt(self, d, url):
        from common import screenshot

        self.wait_for_text(d, 'Bootstrap zipball location')
        time.sleep(.5)
        screenshot(d, 'initial')
        d.ui(className='android.widget.EditText').set_text(url)
        time.sleep(.5)
        screenshot(d, 'entered-url')
        for i in range(2):
            if 'text="OK"' not in d.ui.dump_hierarchy():
                d.ui.press('back')
                time.sleep(.5)
            else:
                break
        time.sleep(.5)
        screenshot(d, 'entered-url-back')
        time.sleep(.5)
        d.ui(text='OK').click()
        screenshot(d, 'ok-clicked')

    def extra_keys(self, d):
        return [html.unescape(text) for text in
                re.findall(r'\btext="([^"]*)"', d.ui.dump_hierarchy())]

    def wake_lock_held(self, d):
        return '(wake lock held)' in d.ui.dump_hierarchy()

    def wait_for_overlay_permission(self, d):
        from common import screenshot

        self.wait_for_text(d, 'Nix requires "Display over other apps" permission')
        self.wait_for_text(d, 'https://dontkillmyapp.com')
        screenshot(d, 'am-wants-permission')
        self.dismiss_am_error(d)

    def dismiss_am_error(self, d):
        from common import screenshot

        time.sleep(3)
        screenshot(d, 'am-wants-permission-3-seconds-later')
        if 'text="TermuxAm Socket Server Error"' in d.ui.dump_hierarchy():
            d.ui.open_notification()
            time.sleep(1)
            screenshot(d, 'notification-opened')
            d.ui(text='TermuxAm Socket Server Error').swipe('right')
            screenshot(d, 'error-notification-swiped-right')
            d.ui.press('back')
            screenshot(d, 'back')

    def check_wake_lock(self, d, held, initial=False):
        from common import screenshot

        if initial:
            d.ui.open_notification()
            screenshot(d, 'notification-opened')
            d.ui(text='Nix').right(resourceId='android:id/expand_button').click()
            screenshot(d, 'notification-expanded')
            self.wait_for_text(d, 'Acquire wakelock')
            screenshot(d, 'wakelock-initially-not-acquired')
            d.ui.press('back')
            return

        if held:
            if 'Let app always run in background?' in d.ui.dump_hierarchy():
                screenshot(d, 'wake-lock-permission-asked')
                self.allow_permission(d)
                screenshot(d, 'wake-lock-permission-granted')
        d.ui.open_notification()
        time.sleep(.5)
        screenshot(d, 'notification-opened')
        if held:
            self.wait_for_text(d, '(wake lock held)')
        action = 'Release wakelock' if held else 'Acquire wakelock'
        if action not in d.ui.dump_hierarchy():
            d.ui(text='Nix').right(resourceId='android:id/expand_button').click()
            screenshot(d, 'notification-expanded')
        self.wait_for_text(d, action)
        screenshot(d, 'notification-with-wakelock' if held
                   else 'notification-without-wakelock')
        d.ui.press('back')
        screenshot(d, 'back')
        self.wait_for_text(d, 'termux-wake-lock' if held else 'termux-wake-unlock')
        screenshot(d, 'really-back')

    def acquire_wake_lock_for_tests(self, d):
        from common import screenshot

        d.ui.open_notification()
        d.ui(text='Nix').right(resourceId='android:id/expand_button').click()
        screenshot(d, 'notification_expanded')
        d.ui(description='Acquire wakelock').click()
        screenshot(d, 'wakelock_acquired')
        d.ui(description='Release wakelock').wait()
        screenshot(d, 'gotta-go-back')
        d.ui.press('back')
        screenshot(d, 'went-back')
