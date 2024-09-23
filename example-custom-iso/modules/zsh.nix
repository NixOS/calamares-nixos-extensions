{
  config,
  lib,
  pkgs,
  modulesPath,
  ...
}:
{
  programs.zsh = {
    enable = true;
    enableCompletion = true;
    autosuggestions.enable = true;
    syntaxHighlighting.enable = true;

    ohMyZsh = {
      enable = true;
      theme = "robbyrussell";
      plugins = [
        "git"
        "history"
        "rust"
        "screen"
        "aliases"
      ];
    };
  };
}
