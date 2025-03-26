{
  config,
  lib,
  pkgs,
  ...
}:

let
  cfg = config.programs.calamares-nixos-extensions-upstream;

  calamaresOptionHelper =
    description:
    (lib.mkOption {
      default = "";
      type = lib.types.str;
      description = description;
    });

  calamares-nixos-autostart = pkgs.makeAutostartItem {
    name = "io.calamares.calamares";
    package = pkgs.calamares-nixos;
  };

  readModulePathsToAttrSet =
    list:
    builtins.listToAttrs (
      map (path: {
        name = (baseNameOf path);
        value = (builtins.readFile path);
      }) list
    );

  createImportsFileStrIfNotEmpty =
    list:
    (
      if (list == [ ]) then
        ""
      else
        (
          ''
            imports = [
          ''
          + lib.concatStringsSep "\n" list
          + "\n"
          + ''
            ];
          ''
        )
    );
in

{
  options.programs.calamares-nixos-extensions-upstream = {
    enable = lib.mkEnableOption "the calamares based NixOS installer";
    autoStart = lib.mkEnableOption " autostart of the installer";

    snippets = {
      modules = lib.mkOption {
        type = lib.types.listOf lib.types.path;
        default = [ ];
        description = "List of module paths that should be available in the installer";
      };

      imports = lib.mkOption {
        type = lib.types.listOf lib.types.str;
        default = [ ];
        description = "List of modules that should be included in configuration.nix";
      };

      desktopEnv = {
        budgie = calamaresOptionHelper "";
        cinnamon = calamaresOptionHelper "";
        deepin = calamaresOptionHelper "";
        enlightment = calamaresOptionHelper "";
        gnome = calamaresOptionHelper "";
        lumnia = calamaresOptionHelper "";
        lxqt = calamaresOptionHelper "";
        mate = calamaresOptionHelper "";
        pantheon = calamaresOptionHelper "";
        plasma6 = calamaresOptionHelper "";
        xfce = calamaresOptionHelper "";
      };

      audio = calamaresOptionHelper "";
      autologin = calamaresOptionHelper "";
      autologindm = calamaresOptionHelper "";
      autologintty = calamaresOptionHelper "";
      bootbios = calamaresOptionHelper "";
      bootefi = calamaresOptionHelper "";
      bootgrubcrypt = calamaresOptionHelper "";
      bootnone = calamaresOptionHelper "";
      connman = calamaresOptionHelper "";
      console = calamaresOptionHelper "";
      extra = calamaresOptionHelper "";
      firefox = calamaresOptionHelper "";
      head = calamaresOptionHelper "";
      keymap = calamaresOptionHelper "";
      locale = calamaresOptionHelper "";
      localextra = calamaresOptionHelper "";
      misc = calamaresOptionHelper "";
      network = calamaresOptionHelper "";
      networkmanager = calamaresOptionHelper "";
      nmapplet = calamaresOptionHelper "";
      pkgs = calamaresOptionHelper "";
      time = calamaresOptionHelper "";
      unfree = calamaresOptionHelper "";
      users = calamaresOptionHelper "";
    };
  };

  ###### implementation

  # nix pkg overlay mit attr over

  config = lib.mkIf cfg.enable {
    environment.systemPackages =
      with pkgs;
      [
        libsForQt5.kpmcore
        calamares-nixos
        calamares-nixos-extensions
        nixfmt-rfc-style
        # Get list of locales
        glibcLocales
      ]
      ++ (lib.optionals (cfg.autoStart) [ calamares-nixos-autostart ]);

    nixpkgs.overlays = [
      (self: super: {
        calamares-nixos-extensions = super.calamares-nixos-extensions.override {
          snippets = cfg.snippets // {
            modules = readModulePathsToAttrSet cfg.snippets.modules;
            imports = createImportsFileStrIfNotEmpty cfg.snippets.imports;
          };
        };
      })
    ];
  };
}
