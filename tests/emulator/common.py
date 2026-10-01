import os
import time

from apps import app


BOOTSTRAP_URL = 'file:///data/local/tmp/n-o-d'


def screenshot(d, suffix=''):
    os.makedirs('screenshots', exist_ok=True)
    fname_base = f'screenshots/{time.time():.3f}-{suffix}'
    d.ui.screenshot(f'{fname_base}.png')
    with open(f'{fname_base}.xml', 'w') as f:
        f.write(d.ui.dump_hierarchy())
    extensions = ['png', 'xml']
    for extension, text in app.screenshot_artifacts(d).items():
        with open(f'{fname_base}.{extension}', 'w') as f:
            f.write(text)
        extensions.append(extension)
    print(f'screenshotted: {fname_base}.{{{",".join(extensions)}}}')


def wait_for(d, on_screen_text, timeout=90, critical=True):
    return app.wait_for_text(d, on_screen_text, timeout=timeout, critical=critical)


def install_and_launch(d):
    nod = app.install(d)
    app.launch(d, nod=nod)
    time.sleep(.5)
    return nod
