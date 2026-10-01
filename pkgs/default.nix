# Copyright (c) 2019-2024, see AUTHORS. Licensed under MIT License, see LICENSE.

{ nixpkgs
, system  # system to compile for, user-facing name of targetSystem
, _nativeSystem ? null  # system to cross-compile from, see flake.nix
, nixOnDroidChannelURL ? null
, nixpkgsChannelURL ? null
, nixOnDroidFlakeURL ? null
  # The Android app the bootstrap is for (`build.androidAppId`); null keeps the
  # module default, the Termux-based app.
, androidAppId ? null
  # Where first boot fetches Nix-on-Droid from when neither the argument above
  # nor its environment variable names a source. A non-default app needs a
  # Nix-on-Droid that has `build.androidAppId`, which the module defaults
  # (this release's branch upstream) may not.
, fallbackNixOnDroidChannelURL ? null
, fallbackNixOnDroidFlakeURL ? null
}:

let
  nativeSystem = if _nativeSystem == null then system else _nativeSystem;
  nixDirectory = callPackage ./nix-directory.nix { inherit system; };
  initialPackageInfo = import "${nixDirectory}/nix-support/package-info.nix";

  pkgs = import nixpkgs { system = nativeSystem; };

  urlOptionValue = url: envVar: fallback:
    let
      envValue = builtins.getEnv envVar;
      value =
        if url != null then url
        else if envValue != "" then envValue
        else fallback;
    in
    pkgs.lib.mkIf (value != null) value;

  modules = import ../modules {
    inherit pkgs;
    targetSystem = system;

    isFlake = true;

    config = {
      imports = [ ../modules/build/initial-build.nix ];

      _module.args = {
        inherit initialPackageInfo;
        pkgs = pkgs.lib.mkForce pkgs; # to override ./modules/nixpkgs/config.nix
      };

      system.stateVersion = "24.05";

      # Fix invoking bash after initial build.
      user.shell = "${initialPackageInfo.bash}/bin/bash";

      build = {
        channel = {
          nixpkgs = urlOptionValue nixpkgsChannelURL "NIXPKGS_CHANNEL_URL" null;
          nix-on-droid = urlOptionValue nixOnDroidChannelURL "NIX_ON_DROID_CHANNEL_URL"
            fallbackNixOnDroidChannelURL;
        };

        flake.nix-on-droid = urlOptionValue nixOnDroidFlakeURL "NIX_ON_DROID_FLAKE_URL"
          fallbackNixOnDroidFlakeURL;
      } // pkgs.lib.optionalAttrs (androidAppId != null) {
        inherit androidAppId;
      };
    };
  };

  callPackage = pkgs.lib.callPackageWith (
    pkgs // customPkgs // {
      inherit (modules) config;
      inherit callPackage nixpkgs nixDirectory initialPackageInfo;
      targetSystem = system;
    }
  );

  customPkgs = {
    bootstrap = callPackage ./bootstrap.nix { };
    bootstrapZip = callPackage ./bootstrap-zip.nix { };
    prootTermux = callPackage ./cross-compiling/proot-termux.nix { };
    tallocStatic = callPackage ./cross-compiling/talloc-static.nix { };
  };
in

{
  inherit (modules) config;
  inherit customPkgs;
}
