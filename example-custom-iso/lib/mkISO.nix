name:
{
  nixpkgs,
  system,
  inputs,
  lib,
  withModules,
  nixosSystem,
}:
nixosSystem rec {
  inherit system;

  modules = withModules ++ [
    (../overlays)
    (
      {
        lib,
        pkgs,
        config,
        ...
      }:
      {
        isoImage.isoName = lib.mkForce "${name}.iso";
      }
    )
  ];
}
