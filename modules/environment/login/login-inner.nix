# Copyright (c) 2019-2023, see AUTHORS. Licensed under MIT License, see LICENSE.

{ config, lib, initialPackageInfo, writeText }:

let
  inherit (initialPackageInfo) cacert nix;

  nixCmd = "${nix}/bin/nix --extra-experimental-features 'flakes nix-command'";
in

writeText "login-inner" ''
  # This file is generated by Nix-on-Droid. DO NOT EDIT.

  set -eo pipefail

  ${lib.optionalString (config.environment.motd != null) ''
    if [ "$#" -eq 0 ]; then  # if script is called from within Nix-on-Droid app
      echo "${lib.removeSuffix "\n" config.environment.motd}"
    fi
  ''}

  ${lib.optionalString config.supervisord.enable ''
    (if [ ! -e "${config.supervisord.socketPath}" ]; then
      ${config.supervisord.package}/bin/supervisord -c /etc/supervisord.conf || echo "Warning: supervisord failed to start"
    fi&)
  ''}

  ${lib.optionalString config.build.initialBuild ''
    if [ -e /etc/UNINTIALISED ]; then
      export HOME="${config.user.home}"
      export USER="${config.user.userName}"

      # To prevent gc warnings of nix, see https://github.com/NixOS/nix/issues/3237
      export GC_NPROCS=1

      echo "Setting default user profile..."
      ${nix}/bin/nix-env --switch-profile /nix/var/nix/profiles/per-user/$USER/profile

      [ "$#" -gt 0 ] || echo "Sourcing Nix environment..."
      . ${nix}/etc/profile.d/nix.sh

      export NIX_SSL_CERT_FILE=${cacert}

      echo
      echo "Nix-on-Droid can be set up with channels or with flakes (still experimental)."
      while [[ -z $USE_FLAKE ]]; do
        read -r -p "Do you want to set it up with flakes? (y/N) " flakes

        if [[ "$flakes" =~ ^[Yy]$ ]]; then
          USE_FLAKE=1
        elif [[ "$flakes" =~ ^[Nn]$ || -z "$flakes" ]]; then
          USE_FLAKE=0
        else
          echo "Received invalid input '$flakes', please try again."
        fi
      done

      if [[ "$USE_FLAKE" == 0 ]]; then

        echo "Setting up Nix-on-Droid with channels..."

        echo "Installing and updating nix-channels..."
        ${nix}/bin/nix-channel --add ${config.build.channel.nixpkgs} nixpkgs
        ${nix}/bin/nix-channel --update nixpkgs
        ${nix}/bin/nix-channel --add ${config.build.channel.nix-on-droid} nix-on-droid
        ${nix}/bin/nix-channel --update nix-on-droid

        DEFAULT_CONFIG=$(${nix}/bin/nix-instantiate --eval --expr "<nix-on-droid/modules/environment/login/nix-on-droid.nix.default>")

        echo "Installing first Nix-on-Droid generation..."
        ${nixCmd} build --no-link --file "<nix-on-droid>" nix-on-droid
        $(${nixCmd} path-info --file "<nix-on-droid>" nix-on-droid)/bin/nix-on-droid switch --file $DEFAULT_CONFIG

        . "${config.user.home}/.nix-profile/etc/profile.d/nix-on-droid-session-init.sh"

        echo "Copying default Nix-on-Droid config..."
        mkdir --parents $HOME/.config/nixpkgs
        cp $DEFAULT_CONFIG $HOME/.config/nixpkgs/nix-on-droid.nix
        chmod u+w $HOME/.config/nixpkgs/nix-on-droid.nix

      else

        echo "Setting up Nix-on-Droid with flakes..."

        echo "Installing flake from default template..."
        ${nixCmd} flake new ${config.user.home}/.config/nix-on-droid --template ${config.build.flake.nix-on-droid}

        ${lib.optionalString config.build.flake.inputOverrides ''
          echo "Overriding input urls in flake..."
          ${nixCmd} run nixpkgs#gnused -- \
            -i \
            -e 's,\"github:NixOS/nixpkgs.*\",\"${config.build.flake.nixpkgs}\",' \
            -e 's,\"github:nix-community/nix-on-droid.*\",\"${config.build.flake.nix-on-droid}\",' \
            "${config.user.home}/.config/nix-on-droid/flake.nix"
        ''}

        echo "Installing first Nix-on-Droid generation..."
        ${nixCmd} run ${config.build.flake.nix-on-droid} -- switch --flake ${config.user.home}/.config/nix-on-droid

        . "${config.user.home}/.nix-profile/etc/profile.d/nix-on-droid-session-init.sh"

      fi

      echo
      echo "Congratulations! Now you have Nix installed with some default packages like bashInteractive, \
    coreutils, cacert and, most importantly, Nix-on-Droid itself to manage local configuration, see"
      echo "  nix-on-droid help"

      if [[ "$USE_FLAKE" == 0 ]]; then
        echo "or the config file"
        echo "  ~/.config/nixpkgs/nix-on-droid.nix"
        echo
        echo "You can go for the bare Nix-on-Droid setup or you can configure your phone via home-manager. See \
    config file for further information."
        echo
      else
        echo "or the flake"
        echo "  ~/.config/nix-on-droid/"
        echo
        echo "You can go for the bare Nix-on-Droid setup or you can configure your phone via home-manager. See \
    other templates in ${config.build.flake.nix-on-droid}."
        echo
      fi
    fi
  ''}

  . "${config.user.home}/.nix-profile/etc/profile.d/nix-on-droid-session-init.sh"

  ${lib.optionalString config.build.initialBuild ''
    exec /usr/bin/env bash  # otherwise it'll be a limited bash that came with Nix
  ''}

  usershell="${config.user.shell}"
  if [ "$#" -gt 0 ]; then  # if script is not called from within Nix-on-Droid app
    exec /usr/bin/env "$@"
  elif [ -x "$usershell" ]; then
    exec -a "-''${usershell##*/}" "$usershell"
  else
    echo "Cannot execute shell '${config.user.shell}', falling back to bash"
    exec -l bash
  fi
''
