# Copyright (c) 2019-2024, see AUTHORS. Licensed under MIT License, see LICENSE.

{ config, lib, pkgs, ... }:

let
  cfg = config.android-integration;

  appId = config.build.androidAppId;

  termux-am =
    pkgs.callPackage (import ../../pkgs/android-integration/termux-am.nix) {
      inherit appId;
      inherit (cfg.am) socketPath;
    };
  termux-tools =
    pkgs.callPackage (import ../../pkgs/android-integration/termux-tools.nix) {
      inherit termux-am appId;
    };
in
{

  ###### interface

  options.android-integration = {

    am.enable = lib.mkOption {
      type = lib.types.bool;
      default = false;
      example = "true";
      description = lib.mdDoc ''
        Provide an `am` (activity manager) command.
        Is not guaranteed to be a real deal, could be of limited compatibility
        with real `am` (like `termux-am`).
      '';
    };

    am.socketPath = lib.mkOption {
      type = lib.types.str;
      # The app says where it listens, like it says which it is
      # (`build.androidAppId`): NIX_ON_DROID_AM_SOCKET in its sessions, which
      # only an impure evaluation (channels) can read; a flake names it.
      default =
        let fromApp = builtins.getEnv "NIX_ON_DROID_AM_SOCKET";
        in if fromApp != "" then fromApp
        else "/data/data/${appId}/files/apps/${appId}/termux-am/am.sock";
      defaultText = lib.literalMD
        "the app's `NIX_ON_DROID_AM_SOCKET`, when the evaluation can see it (channels); else Termux's layout, `/data/data/<id>/files/apps/<id>/termux-am/am.sock`";
      example = "/data/data/org.example.nix/files/apps/termux-am/am.sock";
      description = lib.mdDoc ''
        The Unix socket the app's `am` server listens on, which `am` (and
        so every other tool here) connects to. Termux's layout names the
        app id twice: an app whose id is longer than 33 characters must
        listen somewhere shorter, since a socket path has at most 107
        bytes.
      '';
    };

    termux-open.enable = lib.mkOption {
      type = lib.types.bool;
      default = false;
      example = "true";
      description = lib.mdDoc ''
        Provide a `termux-open` command
        that opens files or urls in external apps
        (uses `com.termux.app.TermuxOpenReceiver`).
      '';
    };

    termux-open-url.enable = lib.mkOption {
      type = lib.types.bool;
      default = false;
      example = "true";
      description = lib.mdDoc ''
        Provide a `termux-open-url` command
        that opens files or urls in external apps
        (uses `android.intent.action.VIEW`).
      '';
    };

    termux-setup-storage.enable = lib.mkOption {
      type = lib.types.bool;
      default = false;
      example = "true";
      description = lib.mdDoc ''
        Provide a `termux-setup-storage` command
        that makes the app request storage permission,
        and then creates a $HOME/storage directory with symlinks to storage.
      '';
    };

    termux-reload-settings.enable = lib.mkOption {
      type = lib.types.bool;
      default = false;
      example = "true";
      description = lib.mdDoc ''
        Provide a `termux-reload-settings` command
        which applies changes to font, colorscheme or terminal
        without the need to close all the sessions.
      '';
    };

    termux-wake-lock.enable = lib.mkOption {
      type = lib.types.bool;
      default = false;
      example = "true";
      description = lib.mdDoc ''
        Provide a `termux-wake-lock` command
        that tones down Android power saving measures.
        This is the same action that's available from the notification.
      '';
    };

    termux-wake-unlock.enable = lib.mkOption {
      type = lib.types.bool;
      default = false;
      example = "true";
      description = lib.mdDoc ''
        Provide a `termux-wake-unlock` command
        that undoes the effect of the `termux-wake-lock` one.
      '';
    };

    xdg-open.enable = lib.mkOption {
      type = lib.types.bool;
      default = false;
      example = "true";
      description = lib.mdDoc ''
        Provide an `xdg-open` alias to `termux-open` command.
      '';
    };

    unsupported.enable = lib.mkOption {
      type = lib.types.bool;
      default = false;
      example = "true";
      description = lib.mdDoc ''
        Provide several more unsupported and untested commands.
        For testing and for brave souls only.
      '';
    };

  };

  ###### implementation

  config = let ifD = cond: pkg: if cond then [ pkg ] else [ ]; in {
    # Every tool here reaches the app through `am`.
    assertions = [{
      assertion = !(lib.any (tool: cfg.${tool}.enable) [
        "am"
        "termux-open"
        "termux-open-url"
        "termux-reload-settings"
        "termux-setup-storage"
        "termux-wake-lock"
        "termux-wake-unlock"
        "xdg-open"
        "unsupported"
      ]) || builtins.stringLength cfg.am.socketPath <= 107;
      message = "android-integration.am.socketPath is ${toString (builtins.stringLength cfg.am.socketPath)} bytes, "
        + "over the 107 a Unix socket path can have; set a shorter one where the app listens "
        + "(${cfg.am.socketPath}).";
    }];

    environment.packages =
      (ifD cfg.am.enable termux-am) ++
      (ifD cfg.termux-setup-storage.enable termux-tools.setup_storage) ++
      (ifD cfg.termux-open.enable termux-tools.open) ++
      (ifD cfg.termux-open-url.enable termux-tools.open_url) ++
      (ifD cfg.termux-reload-settings.enable termux-tools.reload_settings) ++
      (ifD cfg.termux-wake-lock.enable termux-tools.wake_lock) ++
      (ifD cfg.termux-wake-unlock.enable termux-tools.wake_unlock) ++
      (ifD cfg.xdg-open.enable termux-tools.xdg_open) ++
      (ifD cfg.unsupported.enable termux-tools.out);
  };
}
