#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#   SPDX-FileCopyrightText: 2022 Victor Fuentes <vmfuentes64@gmail.com>
#   SPDX-FileCopyrightText: 2019 Adriaan de Groot <groot@kde.org>
#   SPDX-License-Identifier: GPL-3.0-or-later
#
#   Calamares is Free Software: see the License-Identifier above.
#

import configparser
import libcalamares
import os
import subprocess
import re

import gettext

_ = gettext.translation(
    "calamares-python",
    localedir=libcalamares.utils.gettext_path(),
    languages=libcalamares.utils.gettext_languages(),
    fallback=True,
).gettext

def getCalamaresNixosModulePath():
    return '/run/current-system/sw/lib/calamares/modules/nixos'

def getCustomOrDefaultSnippet(snippetName):
    configPath = getCalamaresNixosModulePath()

    # Check if a custom snippet exists for the config name
    snippetConfigPath = '{}/defaultConfigs/snippets/{}.snippet'.format(configPath, snippetName)
    customConfigFilePath = '{}/customConfigs/snippets/{}.snippet'.format(configPath, snippetName)

    if os.path.isfile(customConfigFilePath):
        libcalamares.utils.debug('Selected custom snippet: {} from {}'.format(snippetName, customConfigFilePath))
        snippetConfigPath = customConfigFilePath
    else:
        libcalamares.utils.debug('Selected default snippet: {} from {}'.format(snippetName, snippetConfigPath))

    # load config
    with open(snippetConfigPath, 'r') as configReader:
        snippet = configReader.read()
        snippet += '\n'
        return snippet

    libcalamares.utils.error('Failed to load config snippet {}'.format(snippetName))
    return ""

def copyModules(root_mount_point, subpath):
    customModuleFolderPath = '{}/{}/.'.format(getCalamaresNixosModulePath(), subpath)
    destModuleFolderPath = '{}/etc/nixos/modules/'.format(root_mount_point)
    if not os.path.isdir(destModuleFolderPath):
        libcalamares.utils.host_env_process_output(
            ["mkdir", "-p", destModuleFolderPath], None
        )
    if os.path.isdir(customModuleFolderPath):
        libcalamares.utils.debug('Copying module directory {}'.format(customModuleFolderPath))
        libcalamares.utils.host_env_process_output(["cp", "-r", customModuleFolderPath, destModuleFolderPath], None)
    else:
        libcalamares.utils.debug('Skipping non-existing module directory {}'.format(customModuleFolderPath))

def env_is_set(name):
    envValue = os.environ.get(name)
    return not (envValue is None or envValue == "")

def generateProxyStrings():
    proxyEnv = []
    if env_is_set('http_proxy'):
        proxyEnv.append('http_proxy={}'.format(os.environ.get('http_proxy')))
    if env_is_set('https_proxy'):
        proxyEnv.append('https_proxy={}'.format(os.environ.get('https_proxy')))
    if env_is_set('HTTP_PROXY'):
        proxyEnv.append('HTTP_PROXY={}'.format(os.environ.get('HTTP_PROXY')))
    if env_is_set('HTTPS_PROXY'):
        proxyEnv.append('HTTPS_PROXY={}'.format(os.environ.get('HTTPS_PROXY')))

    if len(proxyEnv) > 0:
        proxyEnv.insert(0, "env")

    return proxyEnv

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

    ngc_cfg = configparser.ConfigParser()
    ngc_cfg["Defaults"] = { "Kernel": "lts" }
    ngc_cfg.read("/etc/nixos-generate-config.conf")

    # Create initial config file
    cfg = getCustomOrDefaultSnippet('head')
    cfg += getCustomOrDefaultSnippet('imports')
    gs = libcalamares.globalstorage
    variables = dict()

    # Setup variables
    root_mount_point = gs.value("rootMountPoint")
    config = os.path.join(root_mount_point, "etc/nixos/configuration.nix")
    fw_type = gs.value("firmwareType")
    bootdev = (
        "nodev"
        if gs.value("bootLoader") is None
        else gs.value("bootLoader")["installPath"]
    )

    # Pick config parts and prepare substitution

    # Check bootloader
    if fw_type == "efi":
        cfg += getCustomOrDefaultSnippet('bootefi')
    elif bootdev != "nodev":
        cfg += getCustomOrDefaultSnippet('bootbios')
        catenate(variables, "bootdev", bootdev)
    else:
        cfg += getCustomOrDefaultSnippet('bootnone')

    if ngc_cfg["Defaults"]["Kernel"] == "latest":
        cfg += getCustomOrDefaultSnippet('latestkernel')

    # Setup encrypted swap devices. nixos-generate-config doesn't seem to notice them.
    for part in gs.value("partitions"):
        if (
            part["claimed"] is True
            and (part["fsName"] == "luks" or part["fsName"] == "luks2")
            and part["device"] is not None
            and part["fs"] == "linuxswap"
        ):
            cfg += """  boot.initrd.luks.devices."{}".device = "/dev/disk/by-uuid/{}";\n""".format(
                part["luksMapperName"], part["uuid"]
            )

    # Check partitions
    root_is_encrypted = False
    boot_is_encrypted = False
    boot_is_partition = False

    for part in gs.value("partitions"):
        if part["mountPoint"] == "/":
            root_is_encrypted = part["fsName"] in ["luks", "luks2"]
        elif part["mountPoint"] == "/boot":
            boot_is_partition = True
            boot_is_encrypted = part["fsName"] in ["luks", "luks2"]

    # Setup keys in /boot/crypto_keyfile if using BIOS and Grub cryptodisk
    if fw_type != "efi" and (
        (boot_is_partition and boot_is_encrypted)
        or (root_is_encrypted and not boot_is_partition)
    ):
        cfg += getCustomOrDefaultSnippet('bootgrubcrypt')
        status = _("Setting up LUKS")
        libcalamares.job.setprogress(0.15)
        try:
            libcalamares.utils.host_env_process_output(
                ["mkdir", "-p", root_mount_point + "/boot"], None
            )
            libcalamares.utils.host_env_process_output(
                ["chmod", "0700", root_mount_point + "/boot"], None
            )
            # Create /boot/crypto_keyfile.bin
            libcalamares.utils.host_env_process_output(
                [
                    "dd",
                    "bs=512",
                    "count=4",
                    "if=/dev/random",
                    "of=" + root_mount_point + "/boot/crypto_keyfile.bin",
                    "iflag=fullblock",
                ],
                None,
            )
            libcalamares.utils.host_env_process_output(
                ["chmod", "600", root_mount_point + "/boot/crypto_keyfile.bin"], None
            )
        except subprocess.CalledProcessError:
            libcalamares.utils.error("Failed to create /boot/crypto_keyfile.bin")
            return (
                _("Failed to create /boot/crypto_keyfile.bin"),
                _("Check if you have enough free space on your partition."),
            )

        for part in gs.value("partitions"):
            if (
                part["claimed"] is True
                and (part["fsName"] == "luks" or part["fsName"] == "luks2")
                and part["device"] is not None
            ):
                cfg += """  boot.initrd.luks.devices."{}".keyFile = "/boot/crypto_keyfile.bin";\n""".format(
                    part["luksMapperName"]
                )
                try:
                    # Grub currently only supports pbkdf2 for luks2
                    libcalamares.utils.host_env_process_output(
                        [
                            "cryptsetup",
                            "luksConvertKey",
                            "--hash",
                            "sha256",
                            "--pbkdf",
                            "pbkdf2",
                            part["device"],
                        ],
                        None,
                        part["luksPassphrase"],
                    )
                    # Add luks drives to /boot/crypto_keyfile.bin
                    libcalamares.utils.host_env_process_output(
                        [
                            "cryptsetup",
                            "luksAddKey",
                            "--hash",
                            "sha256",
                            "--pbkdf",
                            "pbkdf2",
                            part["device"],
                            root_mount_point + "/boot/crypto_keyfile.bin",
                        ],
                        None,
                        part["luksPassphrase"],
                    )
                except subprocess.CalledProcessError:
                    libcalamares.utils.error(
                        "Failed to add {} to /boot/crypto_keyfile.bin".format(
                            part["luksMapperName"]
                        )
                    )
                    return (
                        _("cryptsetup failed"),
                        _(
                            "Failed to add {} to /boot/crypto_keyfile.bin".format(
                                part["luksMapperName"]
                            )
                        ),
                    )

    status = _("Configuring NixOS")
    libcalamares.job.setprogress(0.18)

    cfg += getCustomOrDefaultSnippet('network')
    if gs.value("packagechooser_packagechooser") == "enlightenment":
        cfg += getCustomOrDefaultSnippet('connman')
    else:
        cfg += getCustomOrDefaultSnippet('networkmanager')

    if (
        (gs.value("packagechooser_packagechooser") == "mate")
        | (gs.value("packagechooser_packagechooser") == "lxqt")
        | (gs.value("packagechooser_packagechooser") == "lumina")
    ):
        cfg += getCustomOrDefaultSnippet('nmapplet')

    if gs.value("hostname") is None:
        catenate(variables, "hostname", "nixos")
    else:
        catenate(variables, "hostname", gs.value("hostname"))

    if gs.value("locationRegion") is not None and gs.value("locationZone") is not None:
        cfg += getCustomOrDefaultSnippet('time')
        catenate(
            variables,
            "timezone",
            gs.value("locationRegion"),
            "/",
            gs.value("locationZone"),
        )

    if gs.value("localeConf") is not None:
        localeconf = gs.value("localeConf")
        locale = localeconf.pop("LANG").split("/")[0]
        cfg += getCustomOrDefaultSnippet('locale')
        catenate(variables, "LANG", locale)
        if (
            len(set(localeconf.values())) != 1
            or list(set(localeconf.values()))[0] != locale
        ):
            cfg += getCustomOrDefaultSnippet('localeextra')
            for conf in localeconf:
                catenate(variables, conf, localeconf.get(conf).split("/")[0])

    # Choose desktop environment
    if gs.value("packagechooser_packagechooser") == "gnome":
        cfg += getCustomOrDefaultSnippet('desktopEnv/gnome')
    elif gs.value("packagechooser_packagechooser") == "plasma6":
        cfg += getCustomOrDefaultSnippet('desktopEnv/plasma6')
    elif gs.value("packagechooser_packagechooser") == "xfce":
        cfg += getCustomOrDefaultSnippet('desktopEnv/xfce')
    elif gs.value("packagechooser_packagechooser") == "pantheon":
        cfg += getCustomOrDefaultSnippet('desktopEnv/pantheon')
    elif gs.value("packagechooser_packagechooser") == "cinnamon":
        cfg += getCustomOrDefaultSnippet('desktopEnv/cinnamon')
    elif gs.value("packagechooser_packagechooser") == "mate":
        cfg += getCustomOrDefaultSnippet('desktopEnv/mate')
    elif gs.value("packagechooser_packagechooser") == "enlightenment":
        cfg += getCustomOrDefaultSnippet('desktopEnv/enlightenment')
    elif gs.value("packagechooser_packagechooser") == "lxqt":
        cfg += getCustomOrDefaultSnippet('desktopEnv/lxqt')
    elif gs.value("packagechooser_packagechooser") == "lumina":
        cfg += getCustomOrDefaultSnippet('desktopEnv/lumina')
    elif gs.value("packagechooser_packagechooser") == "budgie":
        cfg += getCustomOrDefaultSnippet('desktopEnv/budgie')
    elif gs.value("packagechooser_packagechooser") == "deepin":
        cfg += getCustomOrDefaultSnippet('desktopEnv/deepin')

    if (
        gs.value("keyboardLayout") is not None
        and gs.value("keyboardVariant") is not None
    ):
        cfg += getCustomOrDefaultSnippet('keymap')
        catenate(variables, "kblayout", gs.value("keyboardLayout"))
        catenate(variables, "kbvariant", gs.value("keyboardVariant"))

        if gs.value("keyboardVConsoleKeymap") is not None:
            try:
                subprocess.check_output(
                    ["pkexec", "loadkeys", gs.value("keyboardVConsoleKeymap").strip()],
                    stderr=subprocess.STDOUT,
                )
                cfg += getCustomOrDefaultSnippet('console')
                catenate(
                    variables, "vconsole", gs.value("keyboardVConsoleKeymap").strip()
                )
            except subprocess.CalledProcessError as e:
                libcalamares.utils.error("loadkeys: {}".format(e.output))
                libcalamares.utils.error(
                    "Setting vconsole keymap to {} will fail, using default".format(
                        gs.value("keyboardVConsoleKeymap").strip()
                    )
                )
        else:
            kbdmodelmap = open(
                "/run/current-system/sw/share/systemd/kbd-model-map", "r"
            )
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
                        ["pkexec", "loadkeys", vconsole], stderr=subprocess.STDOUT
                    )
                    cfg += getCustomOrDefaultSnippet('console')
                    catenate(variables, "vconsole", vconsole)
                except subprocess.CalledProcessError as e:
                    libcalamares.utils.error("loadkeys: {}".format(e.output))
                    libcalamares.utils.error("vconsole value: {}".format(vconsole))
                    libcalamares.utils.error(
                        "Setting vconsole keymap to {} will fail, using default".format(
                            gs.value("keyboardVConsoleKeymap")
                        )
                    )

    if (
        gs.value("packagechooser_packagechooser") is not None
        and gs.value("packagechooser_packagechooser") != ""
    ):
        cfg += getCustomOrDefaultSnippet('misc')
        cfg += getCustomOrDefaultSnippet('audio')

    if gs.value("username") is not None:
        fullname = gs.value("fullname")
        groups = ["networkmanager", "wheel"]

        cfg += getCustomOrDefaultSnippet('users')
        catenate(variables, "username", gs.value("username"))
        catenate(variables, "fullname", fullname)
        catenate(variables, "groups", (" ").join(['"' + s + '"' for s in groups]))
        if (
            gs.value("autoLoginUser") is not None
            and gs.value("packagechooser_packagechooser") is not None
            and gs.value("packagechooser_packagechooser") != ""
        ):
            cfg += getCustomOrDefaultSnippet('autologin')
            if gs.value("packagechooser_packagechooser") == "gnome":
                cfg += getCustomOrDefaultSnippet('autologingdm')
        elif gs.value("autoLoginUser") is not None:
            cfg += getCustomOrDefaultSnippet('autologintty')

    if gs.value("packagechooser_packagechooser") != "":
        cfg += getCustomOrDefaultSnippet('firefox')

    # Check if unfree packages are allowed
    free = True
    if gs.value("packagechooser_unfree") is not None:
        if gs.value("packagechooser_unfree") == "unfree":
            free = False
            cfg += getCustomOrDefaultSnippet('unfree')

    cfg += getCustomOrDefaultSnippet('pkgs')
    # Use firefox as default as a graphical web browser, and add kate to plasma desktop
    if gs.value("packagechooser_packagechooser") == "plasma6":
        catenate(
            variables, "pkgs", "\n      kdePackages.kate\n    #  thunderbird\n    "
        )
    elif gs.value("packagechooser_packagechooser") != "":
        catenate(variables, "pkgs", "\n    #  thunderbird\n    ")
    else:
        catenate(variables, "pkgs", "")

    cfg += getCustomOrDefaultSnippet('extra')

    cfg += getCustomOrDefaultSnippet('tail')
    version = ".".join(subprocess.getoutput(["nixos-version"]).split(".")[:2])[:5]
    catenate(variables, "nixosversion", version)

    # Check that all variables are used
    for key in variables.keys():
        pattern = "@@{key}@@".format(key=key)
        if pattern not in cfg:
            libcalamares.utils.warning("Variable '{key}' is not used.".format(key=key))

    # Check that all patterns exist
    variable_pattern = re.compile(r"@@\w+@@")
    for match in variable_pattern.finditer(cfg):
        variable_name = cfg[match.start() + 2 : match.end() - 2]
        if variable_name not in variables:
            libcalamares.utils.warning(
                "Variable '{key}' is used but not defined.".format(key=variable_name)
            )

    # Do the substitutions
    for key in variables.keys():
        pattern = "@@{key}@@".format(key=key)
        cfg = cfg.replace(pattern, str(variables[key]))

    status = _("Generating NixOS configuration")
    libcalamares.job.setprogress(0.25)

    try:
        # Generate hardware.nix with mounted swap device
        subprocess.check_output(
            ["pkexec", "nixos-generate-config", "--root", root_mount_point],
            stderr=subprocess.STDOUT,
        )
    except subprocess.CalledProcessError as e:
        if e.output is not None:
            libcalamares.utils.error(e.output.decode("utf8"))
        return (_("nixos-generate-config failed"), _(e.output.decode("utf8")))

    # Check for unfree stuff in hardware-configuration.nix
    hf = open(root_mount_point + "/etc/nixos/hardware-configuration.nix", "r")
    htxt = hf.read()
    search = re.search(r"boot\.extraModulePackages = \[ (.*) \];", htxt)

    # Check if any extraModulePackages are defined, and remove if only free packages are allowed
    if search is not None and free:
        expkgs = search.group(1).split(" ")
        for pkg in expkgs:
            p = ".".join(pkg.split(".")[3:])
            # Check package p is unfree
            isunfree = subprocess.check_output(
                [
                    "nix-instantiate",
                    "--eval",
                    "--strict",
                    "-E",
                    "with import <nixpkgs> {{}}; pkgs.linuxKernel.packageAliases.linux_default.{}.meta.unfree".format(
                        p
                    ),
                    "--json",
                ],
                stderr=subprocess.STDOUT,
            )
            if isunfree == b"true":
                libcalamares.utils.warning(
                    "{} is marked as unfree, removing from hardware-configuration.nix".format(
                        p
                    )
                )
                expkgs.remove(pkg)
        hardwareout = re.sub(
            r"boot\.extraModulePackages = \[ (.*) \];",
            "boot.extraModulePackages = [ {}];".format(
                "".join(map(lambda x: x + " ", expkgs))
            ),
            htxt,
        )
        # Write the hardware-configuration.nix file
        libcalamares.utils.host_env_process_output(
            [
                "cp",
                "/dev/stdin",
                root_mount_point + "/etc/nixos/hardware-configuration.nix",
            ],
            None,
            hardwareout,
        )

    # Write the configuration.nix file
    libcalamares.utils.host_env_process_output(["cp", "/dev/stdin", config], None, cfg)
    # Format configuration file
    libcalamares.utils.host_env_process_output(["nixfmt",  config], None)

    # Copy modules
    copyModules(root_mount_point, 'defaultConfigs/modules')
    copyModules(root_mount_point, 'customConfigs/modules')

    status = _("Installing NixOS")
    libcalamares.job.setprogress(0.3)

    # build nixos-install command
    nixosInstallCmd = [ "pkexec" ]
    nixosInstallCmd.extend(generateProxyStrings())
    nixosInstallCmd.extend(
        [
            "nixos-install",
            "--no-root-passwd",
            "--root",
            root_mount_point
        ]
    )

    # Install customizations
    try:
        output = ""
        proc = subprocess.Popen(
            nixosInstallCmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
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
