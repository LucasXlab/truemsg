import pytest

from truemsg.config import ConfigError, load_config


@pytest.mark.parametrize(
    "text",
    [
        "ignore = 42",
        'fail_on = "pass"',
        "[thresholds]\noverlap_low = nan",
        "[thresholds]\noverlap_low = 0.9\noverlap_high = 0.1",
        "[thresholds]\nlarge_diff_lines = true",
        "typo = true",
        "broken [",
    ],
)
def test_bad_configuration_is_rejected(tmp_path, text):
    path = tmp_path / "truemsg.toml"
    path.write_text(text)
    with pytest.raises(ConfigError):
        load_config(str(path))


def test_explicit_missing_file_does_not_fall_back(tmp_path):
    (tmp_path / "truemsg.toml").write_text('fail_on = "warn"')
    with pytest.raises(ConfigError):
        load_config(str(tmp_path / "missing.toml"), str(tmp_path))


def test_config_size_and_links(tmp_path):
    path = tmp_path / "large.toml"
    path.write_text("#" * 65537)
    with pytest.raises(ConfigError):
        load_config(str(path))
    link = tmp_path / "linked.toml"
    link.symlink_to(path)
    with pytest.raises(ConfigError):
        load_config(str(link))
