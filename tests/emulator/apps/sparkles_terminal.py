import html
import time

from .base import AppDriver, Capabilities


class Driver(AppDriver):
    app_id = 'dev.petar_kirov.sparkles.terminal.nix'
    restricted_am_message = 'am: this app answers only the requests of'
    apk = 'nix-on-droid.apk'
    capabilities = Capabilities(
        notifications=False,
        overlay_permission=False,
        restricted_am=True,
        initial_storage_prompt=True,
    )

    def install(self, d):
        nod = super().install(d)
        # The debug APK's GL terminal is invisible to accessibility. Opt in
        # to screen dumps before launch; run-as requires a debuggable APK.
        d(f'run-as {self.app_id} sh -c "mkdir -p files/.debug && '
          'touch files/.debug/screen-dump"')
        return nod

    def wait_until(self, d, condition, description, timeout=90):
        from common import screenshot

        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if condition():
                return
            time.sleep(.1)
        screenshot(d, 'error')
        raise TimeoutError(f'NOT FOUND: {description} after {timeout}s')

    def type_line(self, d, text, enter=True):
        before = self.screen(d) if text else None
        # Native input has bounded per-frame queues. Pace small batches so
        # a whole-command injection cannot overflow them. Partial echoes
        # are not acknowledgements: fish may append a history suggestion.
        for start in range(0, len(text), 8):
            super().type_line(d, text[start:start + 8], enter=False)
            time.sleep(.1)
        if text:
            def echoed():
                screen = self.screen(d)
                return screen != before and screen.rstrip().endswith(text.rstrip())

            self.wait_until(d, echoed, f'input echo: {text}')
        if enter:
            d.ui.press('enter')

    def screen(self, d):
        return d(f'run-as {self.app_id} cat files/.debug/screen.txt',
                 check=False).output

    def contains_text(self, d, text):
        ui = d.ui.dump_hierarchy()
        # Dumps persist behind other activities; hidden terminal text must
        # not satisfy checks intended to prove a return from the browser.
        foreground = f'package="{self.app_id}"' in ui
        return ((foreground and text in self.screen(d))
                or html.escape(text, quote=False) in ui)

    def screenshot_artifacts(self, d):
        return {'txt': self.screen(d)}

    def answer_bootstrap_prompt(self, d, url):
        from common import screenshot
        self.wait_for_text(d, 'Bootstrap zipball location')
        screenshot(d, 'initial')
        self.type_line(d, url)
        screenshot(d, 'entered-url')

    def answer_storage_prompt(self, d):
        from common import screenshot

        self.wait_for_text(d, 'Allow sparkles:terminal to access')
        screenshot(d, 'permission-requested')
        self.allow_permission(d)
        # The native am server replies before requesting permission, then
        # creates the links asynchronously after the dialog is answered.
        self.wait_until(
            d,
            lambda: d(
                f'run-as {self.app_id} sh -c '
                '"test -L files/home/storage/shared && '
                'test -L files/home/storage/pictures"',
                check=False,
            ).returncode == 0,
            'shared storage links',
        )
        screenshot(d, 'permission-granted')

    def extra_keys(self, d):
        return d(f'run-as {self.app_id} cat files/.debug/keys.txt',
                 check=False).output.split()

    def wake_lock_held(self, d):
        return 'sparkles:terminal' in d('dumpsys power').output.split(
            'Wake Locks:')[1].split('Suspend Blockers:')[0]
