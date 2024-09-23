{
  config,
  lib,
  pkgs,
  modulesPath,
  ...
}:

{
  virtualisation.virtualbox.guest = {
    enable = lib.mkForce true;
  };

  # Allow unfree packages
  nixpkgs.config.allowUnfree = true;
}
