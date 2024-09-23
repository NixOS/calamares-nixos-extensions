{
  config,
  nixpkgs,
  pkgs,
  lib,
  ...
}:
{
  nixpkgs.overlays = [
    (final: prev: {
      calamares-nixos-extensions = prev.calamares-nixos-extensions.overrideAttrs (prev: {
        src = pkgs.fetchFromGitHub {
          owner = "friedrichaltheide";
          repo = "calamares-nixos-extensions";
          rev = "ebd43128a652304ce18c920733b5147a690c47eb";
          sha256 = "sha256-PixSYqRonBif7piWjwfCVwC0/w5Tqgz2DwO6RnfPNy8=";
        };
      });
    })
  ];
}
