import sys

import pytest

from app.__main__ import main


@pytest.mark.parametrize("port", ["-1", "65536"])
def test_cli_rejects_out_of_range_port(monkeypatch, capsys, port):
    monkeypatch.setattr(sys, "argv", ["app", "--port", port])

    with pytest.raises(SystemExit) as exc:
        main()

    assert exc.value.code == 2
    assert "--port must be between 0 and 65535" in capsys.readouterr().err
