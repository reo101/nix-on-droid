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

    build.installationDir = "/data/data/com.termux.nix/files/usr";

  };

}
