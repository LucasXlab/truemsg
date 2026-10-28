from truemsg.config import DEFAULTS, is_ignored, load_config


def test_defaults():
    cfg = load_config(start_dir="/nonexistent")
    assert cfg["fail_on"] == "fail"
    assert cfg["thresholds"]["overlap_low"] == DEFAULTS["thresholds"]["overlap_low"]


def test_is_ignored():
    assert is_ignored("generated/schema.go", ["generated/*"])
    assert is_ignored("dist/app.min.js", ["*.min.js"])
    assert not is_ignored("src/main.py", ["generated/*"])


def test_load_from_file(tmp_path):
    p = tmp_path / "truemsg.toml"
    p.write_text('fail_on = "warn"\nignore = ["generated/*"]\n[thresholds]\noverlap_low = 0.5\n')
    cfg = load_config(config_path=str(p))
    assert cfg["fail_on"] == "warn"
    assert "generated/*" in cfg["ignore"]
    assert cfg["thresholds"]["overlap_low"] == 0.5
    # unset thresholds keep defaults
    assert cfg["thresholds"]["large_diff_lines"] == DEFAULTS["thresholds"]["large_diff_lines"]
