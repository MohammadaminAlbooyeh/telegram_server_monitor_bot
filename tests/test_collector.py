"""Tests for metrics collector."""
from unittest.mock import MagicMock

from monitoring.collector import MetricsCollector


class TestMetricsCollector:
    """Test collector helpers."""

    def test_get_cpu_usage_uses_proc_stat_delta(self):
        collector = MetricsCollector(
            {
                "hostname": "localhost",
                "ssh_port": 22,
                "username": "pi",
            }
        )
        collector.ssh_handler = MagicMock()
        collector.ssh_handler.execute_command.side_effect = [
            "1000 980",
            "1100 1035",
        ]

        usage = collector.get_cpu_usage()

        assert 44.0 <= usage <= 56.0
        assert collector.ssh_handler.execute_command.call_count == 2
