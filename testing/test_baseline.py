import subprocess
import os

def read_baseline_cfg(filePath):
    with open(filePath, 'r') as file:
        return file.read()

def test_baseline(
    mocker,
    run,
    mock_gettext_translation,
    mock_libcalamares,
    mock_getoutput,
    mock_check_output,
    mock_open_ngcconf,
    mock_open_hwconf,
    mock_Popen,
):
    result = run()

    assert result is None, "nixos-install failed."

    mock_gettext_translation.assert_called_once_with(
        "calamares-python", localedir=mocker.ANY, languages=mocker.ANY, fallback=True
    )

    # libcalamares.job.setprogress(0.1)
    assert mock_libcalamares.job.setprogress.mock_calls[0] == mocker.call(0.1)



    # libcalamares.job.setprogress(0.18)
    assert mock_libcalamares.job.setprogress.mock_calls[1] == mocker.call(0.18)

    # version = ".".join(subprocess.getoutput(
    # ["nixos-version"]).split(".")[:2])[:5]
    assert mock_getoutput.mock_calls[0] == mocker.call(["nixos-version"])

    # The baseline configuration should not raise any warnings.
    mock_libcalamares.utils.warning.assert_not_called()

    # libcalamares.job.setprogress(0.25)
    assert mock_libcalamares.job.setprogress.mock_calls[2] == mocker.call(0.25)

    # subprocess.check_output(
    #     ["pkexec", "nixos-generate-config", "--root", root_mount_point], stderr=subprocess.STDOUT)
    assert mock_check_output.mock_calls[0] == mocker.call(
        ["pkexec", "nixos-generate-config", "--root", "/mnt/root"],
        stderr=subprocess.STDOUT,
    )

    mock_open_ngcconf.assert_called_once_with(
        "/etc/nixos-generate-config.conf"
    )

    # hf = open(root_mount_point + "/etc/nixos/hardware-configuration.nix", "r")
    mock_open_hwconf.assert_called_once_with(
        "/mnt/root/etc/nixos/hardware-configuration.nix", "r"
    )

    # libcalamares.utils.host_env_process_output(
    #     ["cp", "/dev/stdin", config], None, cfg)
    assert mock_libcalamares.utils.host_env_process_output.mock_calls[0] == mocker.call(
        ["cp", "/dev/stdin", "/mnt/root/etc/nixos/configuration.nix"], None, mocker.ANY
    )
    cfg = mock_libcalamares.utils.host_env_process_output.mock_calls[0].args[2]
    # assert cfg == read_baseline_cfg('{}/baseline_cfg.nix'.format(os.path.dirname(__file__)))

    # libcalamares.utils.host_env_process_output(
    #     ["nixfmt",  config], None)
    mock_libcalamares.utils.host_env_process_output.assert_called_with(
        ["nixfmt", "/mnt/root/etc/nixos/configuration.nix"], None
    )

    # libcalamares.job.setprogress(0.3)
    assert mock_libcalamares.job.setprogress.mock_calls[3] == mocker.call(0.3)

    # proc = subprocess.Popen(["pkexec", "nixos-install", "--no-root-passwd", "--root", root_mount_point], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    mock_Popen.assert_called_once_with(
        ["pkexec", "nixos-install", "--no-root-passwd", "--root", "/mnt/root"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
