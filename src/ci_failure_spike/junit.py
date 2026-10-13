from dataclasses import dataclass

from defusedxml import ElementTree


class JUnitError(ValueError):
    pass


@dataclass(frozen=True)
class Failure:
    node_id: str
    message: str
    detail: str

    @property
    def summary(self) -> str:
        return f"{self.node_id}: {self.message}\n{self.detail}"[:8000]


def parse_failures(body: bytes, max_failures: int) -> list[Failure]:
    try:
        root = ElementTree.fromstring(body)
    except Exception as exc:
        raise JUnitError("invalid or unsafe JUnit XML") from exc

    if root.tag not in {"testsuite", "testsuites"}:
        raise JUnitError("unsupported JUnit root element")

    failures: list[Failure] = []
    for case in root.iter("testcase"):
        failure = case.find("failure")
        if failure is None:
            failure = case.find("error")
        if failure is None:
            continue
        classname = case.attrib.get("classname", "")
        name = case.attrib.get("name", "unknown")
        node_id = f"{classname}::{name}" if classname else name
        failures.append(
            Failure(
                node_id=node_id[:1000],
                message=failure.attrib.get("message", "test failed")[:2000],
                detail=(failure.text or "")[:6000],
            )
        )
        if len(failures) > max_failures:
            raise JUnitError("too many failures")
    if not failures:
        raise JUnitError("report contains no failures")
    return failures

