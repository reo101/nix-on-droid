import bootstrap_channels
from apps import app

from common import screenshot, wait_for


def run(d):
    bootstrap_channels.run(d)

    app.type_line(d, 'zip')
    wait_for(d, 'bash: zip: command not found')
    screenshot(d, 'no-zip')

    # Smoke-test nix-shell + change config + apply config
    app.type_line(d, 'nix-shell -p gnumake -p gnused')
    wait_for(d, '[nix-shell:~]$')
    app.type_line(d, 'make')
    wait_for(d, 'No targets specified and no makefile found.')
    screenshot(d, 'nix-shell-with-make-and-sed')
    # Change config and apply it
    app.type_line(d, 'sed -i "s|#zip|zip|g" .config/nixpkgs/nix-on-droid.nix')
    app.type_line(d, 'exit')
    screenshot(d, 'pre-switch')
    app.type_line(d, 'nix-on-droid switch')
    screenshot(d, 'post-switch')

    # Verify zip is there
    app.type_line(d, 'zip -v | head -n2')
    wait_for(d, 'This is Zip')
    screenshot(d, 'zip-appears')

    # Re-login and make sure login is still operational

    app.type_line(d, 'exit')

    app.launch(d)
    screenshot(d, 're-login')
    wait_for(d, 'Installing new login-inner...')
    wait_for(d, 'bash-5.2$')
    screenshot(d, 're-login-done')

    # And verify zip is still there
    app.type_line(d, 'zip -v | head -n2')
    wait_for(d, 'This is Zip')
    screenshot(d, 'zip-is-still-there')

    def change_shell_and_relogin(shell, descr):
        import base64
        import time
        config = ('{pkgs, ...}: {user.shell = %SHELL%; ' +
                  'system.stateVersion = "24.05";}').replace('%SHELL%', shell)
        config_base64 = base64.b64encode(config.encode()).decode()
        app.type_line(d, f'echo {config_base64} | base64 -d > '
                      '~/.config/nixpkgs/nix-on-droid.nix')
        screenshot(d, f'pre-switch-{descr}')
        app.type_line(d, f'nix-on-droid switch && echo switched  {descr}')
        time.sleep(1)
        screenshot(d, f'in-switch-{descr}')
        wait_for(d, f'switched {descr}')
        screenshot(d, f'post-switch-{descr}')
        app.type_line(d, 'exit')
        screenshot(d, f'pre-re-login-{descr}')
        app.launch(d)
        time.sleep(1)
        screenshot(d, f'post-re-login-{descr}')

    # change shell: pkgs.fish -> fish
    change_shell_and_relogin('pkgs.fish', 'bare-fish')
    wait_for(d, 'Welcome to fish, the friendly interactive shell')
    screenshot(d, 're-login-done-bare-fish')

    # change shell: "${pkgs.fish}", which is a directory -> fallback
    change_shell_and_relogin('"${pkgs.fish}"', 'fish-directory')
    wait_for(d, 'Cannot execute shell ')
    wait_for(d, 'it is a directory.')
    wait_for(d,
             "You should point 'user.shell' to the exact binary.")
    wait_for(d, 'Falling back to bash.')
    wait_for(d, 'bash-5.2$')
    screenshot(d, 're-login-done-shell-dir-fallback')

    # change shell: "${pkgs.fish}/bin/fish" -> fish
    change_shell_and_relogin('"${pkgs.fish}/bin/fish"', 'fish-bin-fish')
    wait_for(d, 'Welcome to fish, the friendly interactive shell')
    screenshot(d, 're-login-done-fish-bin-fish')
