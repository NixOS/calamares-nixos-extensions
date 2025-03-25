name:
{
  system,
  lib,
  withModules,
  nixosSystem,
}:
nixosSystem {
  inherit system;

  modules = withModules ++ [
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
