import html

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

    def extra_keys(self, d):
        return d(f'run-as {self.app_id} cat files/.debug/keys.txt',
                 check=False).output.split()

    def wake_lock_held(self, d):
        return 'sparkles:terminal' in d('dumpsys power').output.split(
            'Wake Locks:')[1].split('Suspend Blockers:')[0]
