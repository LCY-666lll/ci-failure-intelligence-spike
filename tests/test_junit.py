import pytest

from ci_failure_spike.junit import JUnitError, parse_failures


def test_extracts_failure():
    xml = b'''<testsuite><testcase classname="tests.test_api" name="test_failure"><failure message="boom">trace</failure></testcase></testsuite>'''
    failures = parse_failures(xml, 10)
    assert failures[0].node_id == "tests.test_api::test_failure"
    assert failures[0].message == "boom"


def test_rejects_external_entity():
    xml = b'''<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><testsuite><testcase name="x"><failure>&xxe;</failure></testcase></testsuite>'''
    with pytest.raises(JUnitError, match="unsafe"):
        parse_failures(xml, 10)


def test_rejects_reports_without_failures():
    with pytest.raises(JUnitError, match="no failures"):
        parse_failures(b"<testsuite><testcase name='ok'/></testsuite>", 10)

