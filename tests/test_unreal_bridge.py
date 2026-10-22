import pytest

from structuresynth_mcp.unreal_bridge import UnrealNotRunning, send_command


def test_unreachable_raises():
    """If nothing listens on 127.0.0.1:55557, we get a clear error."""
    # Port 1 (privileged, almost certainly closed) as a stand-in for 'not running'.
    import structuresynth_mcp.unreal_bridge as ub

    old_port = ub.UNREAL_PORT
    ub.UNREAL_PORT = 1
    try:
        with pytest.raises(UnrealNotRunning, match="Cannot reach Unreal"):
            send_command("ping", timeout=2)
    finally:
        ub.UNREAL_PORT = old_port
