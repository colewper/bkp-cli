import unittest

from bkp_cli.cli import parse_command


class TestParseCommand(unittest.TestCase):
    def test_config_list(self):
        cmd = parse_command("config list")
        self.assertEqual(cmd.name, "config_list")
        self.assertEqual(cmd.raw_input, "config list")

    def test_config_set(self):
        cmd = parse_command("config set")
        self.assertEqual(cmd.name, "config_set")

    def test_config_clear(self):
        cmd = parse_command("config clear")
        self.assertEqual(cmd.name, "config_clear")

    def test_prepare(self):
        self.assertEqual(parse_command("prepare").name, "prepare")

    def test_commit(self):
        self.assertEqual(parse_command("commit").name, "commit")

    def test_list(self):
        self.assertEqual(parse_command("list").name, "list")

    def test_quit(self):
        self.assertEqual(parse_command("quit").name, "quit")

    def test_whitespace_and_case_insensitive(self):
        self.assertEqual(parse_command("  PREPARE  ").name, "prepare")
        self.assertEqual(parse_command("Config List").name, "config_list")
        self.assertEqual(parse_command("\tCommit\n").name, "commit")
        self.assertEqual(parse_command("  LIST ").name, "list")

    def test_unknown_command(self):
        cmd = parse_command("nonsense")
        self.assertEqual(cmd.name, "unknown")
        self.assertEqual(cmd.raw_input, "nonsense")

    def test_empty_input(self):
        self.assertEqual(parse_command("").name, "unknown")


if __name__ == "__main__":
    unittest.main()
