from truemsg.message import parse_message


def test_conventional_feat():
    m = parse_message("feat(auth): add login endpoint")
    assert m["type"] == "feat"
    assert m["scope"] == "auth"
    assert m["subject"] == "add login endpoint"
    assert m["is_conventional"] is True
    assert "login" in m["keywords"]
    assert "auth" in m["keywords"]


def test_breaking_bang():
    m = parse_message("fix!: drop python2 support")
    assert m["type"] == "fix"
    assert m["breaking"] is True


def test_breaking_in_body():
    m = parse_message("feat: change api\n\nBREAKING CHANGE: removed v1")
    assert m["breaking"] is True


def test_non_conventional():
    m = parse_message("updated some stuff")
    assert m["type"] is None
    assert m["is_conventional"] is False


def test_stopwords_filtered():
    m = parse_message("fix: update the login handler")
    assert "the" not in m["keywords"]
    assert "login" in m["keywords"]
    assert "handler" in m["keywords"]
