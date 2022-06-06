#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#   SPDX-FileCopyrightText: 2022 Victor Fuentes <vmfuentes64@gmail.com>
#   SPDX-FileCopyrightText: 2019 Adriaan de Groot <groot@kde.org>
#   SPDX-License-Identifier: GPL-3.0-or-later
#
#   Calamares is Free Software: see the License-Identifier above.
#

import libcalamares
import os
import subprocess
import re

import gettext
_ = gettext.translation("calamares-python",
                        localedir=libcalamares.utils.gettext_path(),
                        languages=libcalamares.utils.gettext_languages(),
                        fallback=True).gettext


# The following strings contain pieces of a nix-configuration file.
# They are adapted from the default config generated from the nixos-generate-config command.

cfghead = """# Edit this configuration file to define what should be installed on
# your system.  Help is available in the configuration.nix(5) man page
# and in the NixOS manual (accessible by running ‘nixos-help’).

{ config, pkgs, ... }:

{
  imports =
    [ # Include the results of the hardware scan.
      ./hardware-configuration.nix
    ];

"""
cfgbootefi = """  # Bootloader.
  boot.loader.systemd-boot.enable = true;
  boot.loader.efi.canTouchEfiVariables = true;
  boot.loader.efi.efiSysMountPoint = "/boot/efi";

"""

cfgbootbios = """  # Bootloader.
  boot.loader.grub.enable = true;
  boot.loader.grub.device = "@@bootdev@@";
  boot.loader.grub.useOSProber = true;

"""

cfgbootnone = """  # Disable bootloader.
  boot.loader.grub.enable = false;

"""

cfgbootcrypt = """  # Setup keyfile
  boot.initrd.secrets = {
    "/crypto_keyfile.bin" = null;
  };

"""

cfgbootgrubcrypt = """  # Enable grub cryptodisk
  boot.loader.grub.enableCryptodisk=true;

"""

cfgswapcrypt = """  # Enable swap on luks
  boot.initrd.luks.devices."@@swapdev@@".device = "/dev/disk/by-uuid/@@swapuuid@@";
  boot.initrd.luks.devices."@@swapdev@@".keyFile = "/crypto_keyfile.bin";

"""

cfgnetwork = """  networking.hostName = "@@hostname@@"; # Define your hostname.
  # networking.wireless.enable = true;  # Enables wireless support via wpa_supplicant.

  # Configure network proxy if necessary
  # networking.proxy.default = "http://user:password@proxy:port/";
  # networking.proxy.noProxy = "127.0.0.1,localhost,internal.domain";

"""

cfgnetworkmanager = """  # Enable networking
  networking.networkmanager.enable = true;

"""

cfgconnman = """  # Enable networking
  services.connman.enable = true;

"""

cfgnmapplet = """  # Enable network manager applet
  programs.nm-applet.enable = true;

"""

cfgtime = """  # Set your time zone.
  time.timeZone = "@@timezone@@";

"""

cfglocale = """  # Select internationalisation properties.
  i18n.defaultLocale = "@@LANG@@";

"""

cfglocaleextra = """  i18n.extraLocaleSettings = {
    LC_ADDRESS = "@@LC_ADDRESS@@";
    LC_IDENTIFICATION = "@@LC_IDENTIFICATION@@";
    LC_MEASUREMENT = "@@LC_MEASUREMENT@@";
    LC_MONETARY = "@@LC_MONETARY@@";
    LC_NAME = "@@LC_NAME@@";
    LC_NUMERIC = "@@LC_NUMERIC@@";
    LC_PAPER = "@@LC_PAPER@@";
    LC_TELEPHONE = "@@LC_TELEPHONE@@";
    LC_TIME = "@@LC_TIME@@";
  };

"""

cfggnome = """  # Enable the X11 windowing system.
  services.xserver.enable = true;

  # Enable the GNOME Desktop Environment.
  services.xserver.displayManager.gdm.enable = true;
  services.xserver.desktopManager.gnome.enable = true;

"""

cfgplasma = """  # Enable the X11 windowing system.
  services.xserver.enable = true;

  # Enable the KDE Plasma Desktop Environment.
  services.xserver.displayManager.sddm.enable = true;
  services.xserver.desktopManager.plasma5.enable = true;

"""

cfgxfce = """  # Enable the X11 windowing system.
  services.xserver.enable = true;

  # Enable the XFCE Desktop Environment.
  services.xserver.displayManager.lightdm.enable = true;
  services.xserver.desktopManager.xfce.enable = true;

"""

cfgpantheon = """  # Enable the X11 windowing system.
  services.xserver.enable = true;

  # Enable the Pantheon Desktop Environment.
  services.xserver.displayManager.lightdm.enable = true;
  services.xserver.desktopManager.pantheon.enable = true;

"""

cfgcinnamon = """  # Enable the X11 windowing system.
  services.xserver.enable = true;

  # Enable the Cinnamon Desktop Environment.
  services.xserver.displayManager.lightdm.enable = true;
  services.xserver.desktopManager.cinnamon.enable = true;

"""

cfgmate = """  # Enable the X11 windowing system.
  services.xserver.enable = true;

  # Enable the MATE Desktop Environment.
  services.xserver.displayManager.lightdm.enable = true;
  services.xserver.desktopManager.mate.enable = true;

"""

cfgenlightenment = """  # Enable the X11 windowing system.
  services.xserver.enable = true;

  # Enable the Enlightenment Desktop Environment.
  services.xserver.displayManager.lightdm.enable = true;
  services.xserver.desktopManager.enlightenment.enable = true;

  # Enable acpid
  services.acpid.enable = true;

"""

cfglxqt = """  # Enable the X11 windowing system.
  services.xserver.enable = true;

  # Enable the LXQT Desktop Environment.
  services.xserver.displayManager.lightdm.enable = true;
  services.xserver.desktopManager.lxqt.enable = true;

"""

cfglumina = """  # Enable the X11 windowing system.
  services.xserver.enable = true;

  # Enable the Lumina Desktop Environment.
  services.xserver.displayManager.lightdm.enable = true;
  services.xserver.desktopManager.lumina.enable = true;

"""

cfgkeymap = """  # Configure keymap in X11
  services.xserver = {
    layout = "@@kblayout@@";
    xkbVariant = "@@kbvariant@@";
  };

"""
cfgconsole = """  # Configure console keymap
  console.keyMap = "@@vconsole@@";

"""

cfgmisc = """  # Enable CUPS to print documents.
  services.printing.enable = true;

  # Enable sound with pipewire.
  sound.enable = true;
  hardware.pulseaudio.enable = false;
  security.rtkit.enable = true;
  services.pipewire = {
    enable = true;
    alsa.enable = true;
    alsa.support32Bit = true;
    pulse.enable = true;
    # If you want to use JACK applications, uncomment this
    #jack.enable = true;

    # use the example session manager (no others are packaged yet so this is enabled by default,
    # no need to redefine it in your config for now)
    #media-session.enable = true;
  };

  # Enable touchpad support (enabled default in most desktopManager).
  # services.xserver.libinput.enable = true;

"""
cfgusers = """  # Define a user account. Don't forget to set a password with ‘passwd’.
  users.users.@@username@@ = {
    isNormalUser = true;
    description = "@@fullname@@";
    extraGroups = [ @@groups@@ ];
  };

"""

cfgautologin = """  # Enable automatic login for the user.
  services.xserver.displayManager.autoLogin.enable = true;
  services.xserver.displayManager.autoLogin.user = "@@username@@";

"""

cfgautologingdm = """  # Workaround for GNOME autologin: https://github.com/NixOS/nixpkgs/issues/103746#issuecomment-945091229
  systemd.services."getty@tty1".enable = false;
  systemd.services."autovt@tty1".enable = false;

"""

cfgautologintty = """  # Enable automatic login for the user.
  services.getty.autologinUser = "@@username@@";

"""

cfgunfree = """  # Allow unfree packages
  nixpkgs.config.allowUnfree = true;

"""

cfgpkgs = """  # List packages installed in system profile. To search, run:
  # $ nix search wget
  environment.systemPackages = with pkgs; [
  #  vim # Do not forget to add an editor to edit configuration.nix! The Nano editor is also installed by default.
  #  wget@@pkgs@@
  ];

"""

cfgtail = """  # Some programs need SUID wrappers, can be configured further or are
  # started in user sessions.
  # programs.mtr.enable = true;
  # programs.gnupg.agent = {
  #   enable = true;
  #   enableSSHSupport = true;
  # };

  # List services that you want to enable:

  # Enable the OpenSSH daemon.
  # services.openssh.enable = true;

  # Open ports in the firewall.
  # networking.firewall.allowedTCPPorts = [ ... ];
  # networking.firewall.allowedUDPPorts = [ ... ];
  # Or disable the firewall altogether.
  # networking.firewall.enable = false;

  # This value determines the NixOS release from which the default
  # settings for stateful data, like file locations and database versions
  # on your system were taken. It‘s perfectly fine and recommended to leave
  # this value at the release version of the first install of this system.
  # Before changing this value read the documentation for this option
  # (e.g. man configuration.nix or on https://nixos.org/nixos/options.html).
  system.stateVersion = "@@nixosversion@@"; # Did you read the comment?

}
"""


def pretty_name():
    return _("Installing NixOS.")


status = pretty_name()


def pretty_status_message():
    return status


def catenate(d, key, *values):
    """
    Sets @p d[key] to the string-concatenation of @p values
    if none of the values are None.
    This can be used to set keys conditionally based on
    the values being found.
    """
    if [v for v in values if v is None]:
        return

    d[key] = "".join(values)


def run():
    """NixOS Configuration."""

    global status
    status = _("Configuring NixOS")
    libcalamares.job.setprogress(0.1)

    # Create initial config file
    cfg = cfghead
    gs = libcalamares.globalstorage
    variables = dict()

    # Setup variables
    root_mount_point = gs.value("rootMountPoint")
    config = os.path.join(root_mount_point, "etc/nixos/configuration.nix")
    fw_type = gs.value("firmwareType")
    bootdev = "nodev" if gs.value("bootLoader") is None else gs.value(
        "bootLoader")['installPath']

    # Pick config parts and prepare substitution

    # Check bootloader
    if (fw_type == "efi"):
        cfg += cfgbootefi
    elif (bootdev != "nodev"):
        cfg += cfgbootbios
        catenate(variables, "bootdev", bootdev)
    else:
        cfg += cfgbootnone

    # Check partitions
    for part in gs.value("partitions"):
        if part["claimed"] == True and part["fsName"] == "luks":
            cfg += cfgbootcrypt
            if fw_type != "efi":
                cfg += cfgbootgrubcrypt
            status = _("Setting up LUKS")
            libcalamares.job.setprogress(0.15)
            try:
                # Create /crypto_keyfile.bin
                libcalamares.utils.host_env_process_output(
                    ["dd", "bs=512", "count=4", "if=/dev/random", "of="+root_mount_point+"/crypto_keyfile.bin", "iflag=fullblock"], None)
                libcalamares.utils.host_env_process_output(
                    ["chmod", "600", root_mount_point+"/crypto_keyfile.bin"], None)
            except subprocess.CalledProcessError:
                libcalamares.utils.error(
                    "Failed to create /crypto_keyfile.bin")
                return (_("Failed to create /crypto_keyfile.bin"), _("Check if you have enough free space on your partition."))
            break

    # Setup keys in /crypto_keyfile. If we use systemd-boot (EFI), don't add /
    # Goal is to have one password prompt when booted
    for part in gs.value("partitions"):
        if part["claimed"] == True and part["fsName"] == "luks" and part["device"] is not None and not (fw_type == "efi" and part["mountPoint"] == "/"):
            if part["fs"] == "linuxswap":
                cfg += cfgswapcrypt
                catenate(variables, "swapdev", part["luksMapperName"])
                uuid = part["uuid"]
                catenate(variables, "swapuuid", uuid)
            else:
                cfg += """  boot.initrd.luks.devices."{}".keyFile = "/crypto_keyfile.bin";\n""".format(
                    part["luksMapperName"])

            try:
                # Add luks drives to /crypto_keyfile.bin
                libcalamares.utils.host_env_process_output(
                    ["cryptsetup", "luksAddKey", part["device"], root_mount_point+"/crypto_keyfile.bin"], None, part["luksPassphrase"])
            except subprocess.CalledProcessError:
                libcalamares.utils.error(
                    "Failed to add {} to /crypto_keyfile.bin".format(part["luksMapperName"]))
                return (_("cryptsetup failed"), _("Failed to add {} to /crypto_keyfile.bin".format(part["luksMapperName"])))

    status = _("Configuring NixOS")
    libcalamares.job.setprogress(0.18)

    cfg += cfgnetwork
    if gs.value("packagechooser_packagechooser") == "enlightenment":
        cfg += cfgconnman
    else:
        cfg += cfgnetworkmanager

    if (gs.value("packagechooser_packagechooser") == "mate") | (gs.value("packagechooser_packagechooser") == "lxqt") | (gs.value("packagechooser_packagechooser") == "lumina"):
        cfg += cfgnmapplet

    if (gs.value("hostname") is None):
        catenate(variables, "hostname", "nixos")
    else:
        catenate(variables, "hostname", gs.value("hostname"))

    if (gs.value("locationRegion") is not None and gs.value("locationZone") is not None):
        cfg += cfgtime
        catenate(variables, "timezone", gs.value(
            "locationRegion"), "/", gs.value("locationZone"))

    if (gs.value("localeConf") is not None):
        localeconf = gs.value("localeConf")
        locale = localeconf.pop("LANG")
        cfg += cfglocale
        catenate(variables, "LANG", locale)
        if (len(set(localeconf.values())) != 1 or list(set(localeconf.values()))[0] != locale):
            cfg += cfglocaleextra
            for conf in localeconf:
                catenate(variables, conf, localeconf.get(conf))

    # Choose desktop environment
    if gs.value("packagechooser_packagechooser") == "gnome":
        cfg += cfggnome
    elif gs.value("packagechooser_packagechooser") == "plasma":
        cfg += cfgplasma
    elif gs.value("packagechooser_packagechooser") == "xfce":
        cfg += cfgxfce
    elif gs.value("packagechooser_packagechooser") == "pantheon":
        cfg += cfgpantheon
    elif gs.value("packagechooser_packagechooser") == "cinnamon":
        cfg += cfgcinnamon
    elif gs.value("packagechooser_packagechooser") == "mate":
        cfg += cfgmate
    elif gs.value("packagechooser_packagechooser") == "enlightenment":
        cfg += cfgenlightenment
    elif gs.value("packagechooser_packagechooser") == "lxqt":
        cfg += cfglxqt
    elif gs.value("packagechooser_packagechooser") == "lumina":
        cfg += cfglumina

    if (gs.value("keyboardLayout") is not None and gs.value("keyboardVariant") is not None):
        cfg += cfgkeymap
        catenate(variables, "kblayout", gs.value("keyboardLayout"))
        catenate(variables, "kbvariant", gs.value("keyboardVariant"))

        if (gs.value("keyboardVConsoleKeymap") is not None):
            try:
                subprocess.check_output(["pkexec", "loadkeys", gs.value(
                    "keyboardVConsoleKeymap").strip()], stderr=subprocess.STDOUT)
                cfg += cfgconsole
                catenate(variables, "vconsole", gs.value(
                    "keyboardVConsoleKeymap").strip())
            except subprocess.CalledProcessError as e:
                libcalamares.utils.error("loadkeys: {}".format(e.output))
                libcalamares.utils.error("Setting vconsole keymap to {} will fail, using default".format(
                    gs.value("keyboardVConsoleKeymap").strip()))
        else:
            kbdmodelmap = open(
                "/run/current-system/sw/share/systemd/kbd-model-map", 'r')
            kbd = kbdmodelmap.readlines()
            out = []
            for line in kbd:
                if line.startswith("#"):
                    continue
                out.append(line.split())
            # Find rows with same layout
            find = []
            for row in out:
                if gs.value("keyboardLayout") == row[1]:
                    find.append(row)
            if find != []:
                vconsole = find[0][0]
            else:
                vconsole = ""
            if gs.value("keyboardVariant") is not None:
                variant = gs.value("keyboardVariant")
            else:
                variant = "-"
            # Find rows with same variant
            for row in find:
                if variant in row[3]:
                    vconsole = row[0]
                    break
                # If none found set to "us"
            if vconsole != "" and vconsole != "us" and vconsole is not None:
                try:
                    subprocess.check_output(
                        ["pkexec", "loadkeys", vconsole], stderr=subprocess.STDOUT)
                    cfg += cfgconsole
                    catenate(variables, "vconsole", vconsole)
                except subprocess.CalledProcessError as e:
                    libcalamares.utils.error("loadkeys: {}".format(e.output))
                    libcalamares.utils.error(
                        "vconsole value: {}".format(vconsole))
                    libcalamares.utils.error("Setting vconsole keymap to {} will fail, using default".format(
                        gs.value("keyboardVConsoleKeymap")))

    if gs.value("packagechooser_packagechooser") is not None and gs.value("packagechooser_packagechooser") != "":
        cfg += cfgmisc

    if (gs.value("username") is not None):
        fullname = gs.value("fullname")
        groups = ["networkmanager", "wheel"]

        cfg += cfgusers
        catenate(variables, "username", gs.value("username"))
        catenate(variables, "fullname", fullname)
        catenate(variables, "groups", (" ").join(
            ["\"" + s + "\"" for s in groups]))
        if (gs.value("autoLoginUser") is not None and gs.value("packagechooser_packagechooser") is not None and gs.value("packagechooser_packagechooser") != ""):
            cfg += cfgautologin
            if (gs.value("packagechooser_packagechooser") == "gnome"):
                cfg += cfgautologingdm
        elif (gs.value("autoLoginUser") is not None):
            cfg += cfgautologintty

    # Check if unfree packages are allowed
    free = True
    if gs.value("packagechooser_unfree") is not None:
        if gs.value("packagechooser_unfree") == "unfree":
            free = False
            cfg += cfgunfree

    cfg += cfgpkgs
    # Use Brave as default as a graphical web browser, and add kate to plasma desktop
    if gs.value("packagechooser_packagechooser") == "plasma":
        catenate(variables, "pkgs", "\n    brave\n    kate\n    discover\n    appstream-qt")
    elif gs.value("packagechooser_packagechooser") == "gnome":
        catenate(variables, "pkgs", "\n    brave\n    gnome-software\n    appstream")
    elif gs.value("packagechooser_packagechooser") != "":
        catenate(variables, "pkgs", "\n    brave")
    else:
        catenate(variables, "pkgs", "")

    cfg += cfgtail
    version = ".".join(subprocess.getoutput(
        ["nixos-version"]).split(".")[:2])[:5]
    catenate(variables, "nixosversion", version)

    # Check that all variables are used
    for key in variables.keys():
        pattern = "@@{key}@@".format(key=key)
        if not pattern in cfg:
            libcalamares.utils.warning(
                "Variable '{key}' is not used.".format(key=key))

    # Check that all patterns exist
    variable_pattern = re.compile("@@\w+@@")
    for match in variable_pattern.finditer(cfg):
        variable_name = cfg[match.start()+2:match.end()-2]
        if not variable_name in variables:
            libcalamares.utils.warning(
                "Variable '{key}' is used but not defined.".format(key=variable_name))

    # Do the substitutions
    for key in variables.keys():
        pattern = "@@{key}@@".format(key=key)
        cfg = cfg.replace(pattern, str(variables[key]))

    # Mount swap partition
    for part in gs.value("partitions"):
        if part["claimed"] == True and part["fs"] == "linuxswap":
            status = _("Mounting swap")
            libcalamares.job.setprogress(0.2)
            if part["fsName"] == "luks":
                try:
                    libcalamares.utils.host_env_process_output(
                        ["swapon", "/dev/mapper/" + part["luksMapperName"]], None)
                except subprocess.CalledProcessError:
                    libcalamares.utils.error(
                        "Failed to activate swap: " + "/dev/mapper/" + part["luksMapperName"])
                    return (_("swapon failed to activate swap"), _("failed while activating:" + "/dev/mapper/" + part["luksMapperName"]))
            else:
                try:
                    libcalamares.utils.host_env_process_output(
                        ["swapon", part["device"]], None)
                except subprocess.CalledProcessError:
                    libcalamares.utils.error(
                        "Failed to activate swap: " + "/dev/mapper/" + part["device"])
                    return (_("swapon failed to activate swap " + part["device"]), _("failed while activating:" + "/dev/mapper/" + part["device"]))
            break

    status = _("Generating NixOS configuration")
    libcalamares.job.setprogress(0.25)

    try:
        # Generate hardware.nix with mounted swap device
        subprocess.check_output(
            ["pkexec", "nixos-generate-config", "--root", root_mount_point], stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        if e.output != None:
            libcalamares.utils.error(e.output.decode("utf8"))
        return (_("nixos-generate-config failed"), _(e.output.decode("utf8")))

    # Check for unfree stuff in hardware-configuration.nix
    hf = open(root_mount_point + "/etc/nixos/hardware-configuration.nix", "r")
    htxt = hf.read()
    search = re.search("boot\.extraModulePackages = \[ (.*) \];", htxt)

    # Check if any extraModulePackages are defined, and remove if only free packages are allowed
    if search is not None and free:
        expkgs = search.group(1).split(" ")
        for pkg in expkgs:
            p = ".".join(pkg.split(".")[3:])
            # Check package p is unfree
            isunfree = subprocess.check_output(["nix-instantiate", "--eval", "--strict", "-E",
                                               "with import <nixpkgs> {{}}; pkgs.linuxKernel.packageAliases.linux_default.{}.meta.unfree".format(p), "--json"], stderr=subprocess.STDOUT)
            if isunfree == b'true':
                libcalamares.utils.warning(
                    "{} is marked as unfree, removing from hardware-configuration.nix".format(p))
                expkgs.remove(pkg)
        hardwareout = re.sub(
            "boot\.extraModulePackages = \[ (.*) \];", "boot.extraModulePackages = [ {}];".format("".join(map(lambda x: x+" ", expkgs))), htxt)
        # Write the hardware-configuration.nix file
        libcalamares.utils.host_env_process_output(["cp", "/dev/stdin",
                                                    root_mount_point+"/etc/nixos/hardware-configuration.nix"], None, hardwareout)

    # Write the configuration.nix file
    libcalamares.utils.host_env_process_output(
        ["cp", "/dev/stdin", config], None, cfg)

    status = _("Installing NixOS")
    libcalamares.job.setprogress(0.3)

    # Install customizations
    try:
        output = ""
        proc = subprocess.Popen(["pkexec", "nixos-install", "--no-root-passwd", "--root", root_mount_point], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        while True:
            line = proc.stdout.readline().decode("utf-8")
            output += line
            libcalamares.utils.debug("nixos-install: {}".format(line.strip()))
            if not line:
                break
        exit = proc.wait()
        if exit != 0:
            return (_("nixos-install failed"), _(output))
    except:
        return (_("nixos-install failed"), _("Installation failed to complete"))

    return None
