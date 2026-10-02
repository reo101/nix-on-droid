# Copyright (c) 2019-2024, see AUTHORS. Licensed under MIT License, see LICENSE.

{ config, lib, pkgs, ... }:

with lib;

let
  defaultNixpkgsBranch = "nixos-24.05";
  defaultNixOnDroidBranch = "release-24.05";

  defaultNixpkgsChannel = "https://nixos.org/channels/${defaultNixpkgsBranch}";
  defaultNixOnDroidChannel = "https://github.com/nix-community/nix-on-droid/archive/${defaultNixOnDroidBranch}.tar.gz";

  defaultNixpkgsFlake = "github:NixOS/nixpkgs/${defaultNixpkgsBranch}";
  defaultNixOnDroidFlake = "github:nix-community/nix-on-droid/${defaultNixOnDroidBranch}";
in

{

  ###### interface

  options = {

    build = {
      channel = {
        nixpkgs = mkOption {
          type = types.str;
          default = defaultNixpkgsChannel;
          description = "Channel URL for nixpkgs.";
        };

        nix-on-droid = mkOption {
          type = types.str;
          default = defaultNixOnDroidChannel;
          description = "Channel URL for Nix-on-Droid.";
        };
      };

      flake = {
        nixpkgs = mkOption {
          type = types.str;
          default = defaultNixpkgsFlake;
          description = "Flake URL for nixpkgs.";
        };

        nix-on-droid = mkOption {
          type = types.str;
          default = defaultNixOnDroidFlake;
          description = "Flake URL for Nix-on-Droid.";
        };

        inputOverrides = mkEnableOption "" // {
          description = ''
            Whether to override the standard input URLs in the initial <filename>flake.nix</filename>.
          '';
        };
      };

      initialSettings = mkOption {
        type = with types; attrsOf (oneOf [ bool int str ]);
        default = { };
        example = { "android-integration.am.enable" = true; };
        description = ''
          Settings the user's first configuration starts with, by option
          path: first boot writes them into it (below
          <option>system.stateVersion</option>) before its first switch,
          after <option>build.androidAppId</option> when the app is not the
          Termux-based one. For what the app a bootstrap is built for
          provides, such as the <option>android-integration</option> tools
          it serves.
        '';
      };
    };

  };


  ###### implementation

  config = {

    build = {
      initialBuild = true;

      flake.inputOverrides =
        config.build.flake.nixpkgs != defaultNixpkgsFlake
        || config.build.flake.nix-on-droid != defaultNixOnDroidFlake;
    };

    # /etc/group and /etc/passwd need to be build on target machine because
    # uid and gid need to be determined.
    environment.etc = {
      "group".enable = false;
      "passwd".enable = false;
      "UNINTIALISED".text = "";
    };

  };

}
