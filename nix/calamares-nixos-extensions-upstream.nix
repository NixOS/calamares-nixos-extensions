{
  lib,
  ...
}:
{
  imports = [
    ./calamares-nixos-extensions/module.nix
  ];

  nixpkgs.overlays = lib.mkBefore [
    (final: prev: {
      calamares-nixos-extensions = final.callPackage ./calamares-nixos-extensions/package.nix { };
    })
  ];

  programs.calamares-nixos-extensions-upstream = {
    enable = true;
    autoStart = true;
  };

  # TODO disable programs.calamres-nixos-extensions (from nixpkgs)
}
