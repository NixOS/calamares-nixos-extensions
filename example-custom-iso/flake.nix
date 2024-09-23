{
  description = "A custom NixOS calamares installer";

  inputs = {
    # nixpkgs.url = "github:nixos/nixpkgs/nixos-24.05";
    nixpkgs.url = "github:friedrichaltheide/nixpkgs/calamares-nixos-extensions-custom-installer";
  };

  outputs =
    { self, nixpkgs }@inputs:
    let
      mkISO = (import ./lib/mkISO.nix);
      lib = nixpkgs.lib;
      nixosSystem = import (nixpkgs + "/nixos/lib/eval-config.nix");
      system = "x86_64-linux";
    in
    {
      defaultCalamaresIso = mkISO "customCalamaresISO" {
        inherit
          nixpkgs
          inputs
          lib
          system
          ;
        withModules = [
          "${nixpkgs}/nixos/modules/installer/cd-dvd/installation-cd-graphical-calamares-gnome.nix"
        ];
        nixosSystem = nixosSystem;
      };

      customCalamaresISO = mkISO "customCalamaresISO" {
        inherit
          nixpkgs
          inputs
          lib
          system
          ;
        withModules = [
          "${nixpkgs}/nixos/modules/installer/cd-dvd/installation-cd-graphical-calamares-gnome.nix"
          # Add custom modules to the iso
          ./modules/virtualboxGuest.nix
          ./modules/zsh.nix
          # Configure the calamares extension with custom snippets
          (./custom-calamares)
        ];
        nixosSystem = nixosSystem;
      };
    };
}
