{
  config,
  pkgs,
  lib,
  inputs,
  ...
}:
{
  programs.calamares-nixos-extensions = {
    enable = true;
    autoStart = true;
    snippets = {
      # The following strings replace the `imports` in the final configuation.nix
      imports = [
        "./hardware-configuration.nix"
        "./modules/zsh.nix"
        "./modules/virtualboxGuest.nix"
      ];

      # The following nix files are copied to /etc/nixos/modules/ and can then be included using `imports`
      modules = [
        ../modules/zsh.nix
        ../modules/virtualboxGuest.nix
      ];

      # default snippets can also be removed, by setting the snippet to an empty string
      unfree = '''';

      bootefi = ''
        # Bootloader.
        boot.loader.systemd-boot = {
          enable = true;
          configurationLimit = 10;
        };
        boot.loader.efi.canTouchEfiVariables = true;
        boot.tmp.useTmpfs = true;
      '';

      network = ''
        networking.hostName = "@@hostname@@"; # Define your hostname.
        # networking.wireless.enable = true;  # Enables wireless support via wpa_supplicant.
        services.avahi.enable = false;
      '';

      pkgs = ''
        # List packages installed in system profile. To search, run:
        # $ nix search wget
        environment.systemPackages = with pkgs; [
            vim # Do not forget to add an editor to edit configuration.nix! The Nano editor is also installed by default.
            xdg-utils
            git
            htop
        ];

        programs.screen = {
          enable = true;
          screenrc = "caption always \"%{rw} * | %H * $LOGNAME | %{bw}%c %D | %{-}%-Lw%{rw}%50>%{rW}%n%f* %t %{-}%+Lw%<\"";
        };

        environment.interactiveShellInit = '''
          alias open="xdg-open";
        ''';
      '';

      users = ''
        users.users.@@username@@ = {
          isNormalUser = true;
          description = "@@fullname@@";
          extraGroups = [ @@groups@@ ];
          openssh.authorizedKeys.keys = [];
        };
      '';

      extra = ''
        services.openssh = {
          enable = true;
          settings.PasswordAuthentication = false;
          settings.KbdInteractiveAuthentication = false;
        };
      '';
    };
  };
}
