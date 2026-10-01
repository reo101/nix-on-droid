import html
import os
import shlex
import sys
import time
from dataclasses import dataclass


DEFAULT_APP_ID = 'com.termux.nix'


@dataclass(frozen=True)
class Capabilities:
    notifications: bool
    overlay_permission: bool
    restricted_am: bool
    initial_storage_prompt: bool


class AppDriver:
    """Device-independent metadata and overridable emulator interactions."""

    @property
    def files_dir(self):
        return f'/data/data/{self.app_id}/files'

    def install(self, d):
        nod = d.app(self.app_id, url=os.environ.get('NOD_APK', self.apk))
        if self.capabilities.notifications:
            nod.permissions.allow_notifications()
        return nod

    def launch(self, d, nod=None):
        (nod if nod is not None else d.app(self.app_id)).launch()

    def contains_text(self, d, text):
        return html.escape(text, quote=False) in d.ui.dump_hierarchy()

    def wait_for_text(self, d, text, timeout=90, critical=True):
        from common import screenshot

        start = time.time()
        last_displayed_time = None
        while (elapsed := time.time() - start) < timeout:
            display_time = int(timeout - elapsed)
            if display_time != last_displayed_time:
                print(f'waiting for `{text}`: {display_time}s...')
                sys.stdout.flush()
                last_displayed_time = display_time
            if self.contains_text(d, text):
                print(f'found: {text} after {elapsed:.1f}s')
                return
            time.sleep(.75)
        print(f'NOT FOUND: {text} after {timeout}s')
        screenshot(d, suffix='error')
        if critical:
            sys.exit(1)

    def type_line(self, d, text, enter=True):
        if text:
            d(f'input text {shlex.quote(text)}')
        if enter:
            d.ui.press('enter')

    def answer_bootstrap_prompt(self, d, url):
        raise NotImplementedError

    def extra_keys(self, d):
        raise NotImplementedError

    def wake_lock_held(self, d):
        raise NotImplementedError

    def screenshot_artifacts(self, d):
        """Additional textual artifacts, keyed by extension (without a dot)."""
        return {}

    def allow_permission(self, d):
        if 'text="Allow"' in d.ui.dump_hierarchy():
            d.ui(text='Allow').click()
        elif 'text="ALLOW"' in d.ui.dump_hierarchy():
            d.ui(text='ALLOW').click()

    def answer_storage_prompt(self, d):
        from common import screenshot

        self.wait_for_text(d, 'Allow Nix to access')
        screenshot(d, 'permission-requested')
        self.allow_permission(d)
        screenshot(d, 'permission-granted')

    def wait_for_overlay_permission(self, d):
        raise NotImplementedError

    def check_wake_lock(self, d, held, initial=False):
        assert self.wake_lock_held(d) == held

    def acquire_wake_lock_for_tests(self, d):
        raise NotImplementedError
