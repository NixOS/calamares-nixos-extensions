{
  description = "Testing calamares-nixos-extensions";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs =
    { nixpkgs, ... }:
    let
      system = "x86_64-linux";

      pkgs = import nixpkgs {
        inherit system;
      };

      packages = [
        (pkgs.python3.withPackages (
          pp: with pp; [
            pytest
            pytest-mock
          ]
        ))
      ];

      mkISO = (import ./nix/lib/mkISO.nix);
      calamaresIsoBuilder =
        nixpkgsSource: name: extraModules:
        (mkISO name {
          inherit
            system
            ;
          inherit (nixpkgsSource) lib;
          nixosSystem = import (nixpkgsSource + "/nixos/lib/eval-config.nix");
          withModules = [
            "${nixpkgs}/nixos/modules/installer/cd-dvd/installation-cd-graphical-calamares-gnome.nix"
            ./nix/calamares-nixos-extensions-upstream.nix
          ] ++ extraModules;
        }).config.system.build.isoImage;
    in
    {
      packages.${system} = {
        default = pkgs.writeShellApplication {
          name = "test-nixos-install";
          runtimeInputs = packages;
          text = ''
            #!${pkgs.stdenv.shell}
            pytest -vv testing
          '';
        };

        calamares-nixos-extensions = pkgs.callPackage ./nix/calamares-nixos-extensions/package.nix { };

        defaultCalamaresIso = calamaresIsoBuilder nixpkgs "defaultCalamaresISO" [ ];

        customCalamaresIso = calamaresIsoBuilder nixpkgs "customCalamaresISO" [
          # Add custom modules to the iso (runtime)
          ./nix/modules/virtualboxGuest.nix
          ./nix/modules/zsh.nix
          # Configure the calamares extension with custom snippets
          ./nix/modules/calamares-customizations.nix
        ];
      };

      devShells.${system}.default = pkgs.mkShell {
        inherit packages;
      };
    };
}
