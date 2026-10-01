# Copyright (c) 2019-2024, see AUTHORS. Licensed under MIT License, see LICENSE.

{ config, lib, pkgs, ... }:

with lib;

{

  ###### interface

  options = {

    build = {
      initialBuild = mkOption {
        type = types.bool;
        default = false;
        internal = true;
        description = ''
          Whether this is the initial build for the bootstrap zip ball.
          Should not be enabled manually, see
          <filename>initial-build.nix</filename>.
        '';
      };

      androidAppId = mkOption {
        type = types.str;
        # The app says which it is: Termux-based apps export
        # TERMUX_APP__PACKAGE_NAME into their sessions, and an alternative
        # app should too. Only an impure evaluation (channels) can read it; a
        # flake's configuration names the app itself (its first start writes
        # the option into the template).
        default =
          let fromApp = builtins.getEnv "TERMUX_APP__PACKAGE_NAME";
          in if fromApp != "" then fromApp else "com.termux.nix";
        defaultText = literalMD
          "the app's `TERMUX_APP__PACKAGE_NAME`, when the evaluation can see it (channels); else `\"com.termux.nix\"`";
        example = "org.example.nix";
        description = ''
          Package id of the Android app that runs this Nix-on-Droid
          installation. The app's data directory, and therefore
          <option>build.installationDir</option>, <option>user.home</option>
          and the paths of the Android integration tools, derive from it.
          The default is the app running the evaluation, where it can be
          seen, else the Termux-based Nix-on-Droid app. An alternative app
          needs a bootstrap built for its id
          (<literal>lib.bootstrapPackages</literal>). Changing it on an existing installation does not move the
          installation: it must match the app that is actually installed.
        '';
      };

      installationDir = mkOption {
        type = types.path;
        internal = true;
        readOnly = true;
        description = "Path to installation directory.";
      };

      extraProotOptions = mkOption {
        type = types.listOf types.str;
        default = [ ];
        description = "Extra options passed to proot, e.g., extra bind mounts.";
      };

      # When sessions do not use proot (e.g. launcher-based replacements),
      # skipping this keeps evaluation pure: `files.prootStatic` is a
      # hardcoded store-path string whose `types.package` merge calls
      # `builtins.storePath`, which pure evaluation (deploy-rs) rejects.
      linkProotStatic = mkOption {
        type = types.bool;
        default = true;
        description = "Whether the activation package exposes proot-static.";
      };
    };

  };


  ###### implementation

  config = {

    build.installationDir = "/data/data/${config.build.androidAppId}/files/usr";

  };

}
