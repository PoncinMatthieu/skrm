
import os
import unittest
import mock

from skrm.keyring_manager import KeyringManager


class TestKeyringManager(unittest.TestCase):
    # todo: add test for user prefs

    @classmethod
    def setUpClass(cls):
        cls.bdd_filename = "test_bdd.gpg"
        cls.bdd_filename = "test_bdd.gpg"
        cls.default_arguments = ["--recipient=Poncin Matthieu"]

    def setUp(self):
        self._clean_bdd()

    def test_instanciate(self):
        KeyringManager("", "", [])
        KeyringManager("", "", ["--recipient=fake_recipient"])
        KeyringManager("", "", ["--pass=fake_master_pass"])
        KeyringManager("", "", ["--clip"])

        tags = ["tag1", "tag2", "tag3"]
        keyring_manager = KeyringManager("", "", tags)
        self.assertEqual(keyring_manager.tags, tags)

        with self.assertRaises(SystemExit) as cm:
            KeyringManager("", "", ["--help"])
        self.assertEqual(cm.exception.code, 0)

        with self.assertRaises(SystemExit) as cm:
            KeyringManager("", "", ["-h"])
        self.assertEqual(cm.exception.code, 0)

        with self.assertRaises(SystemExit) as cm:
            KeyringManager("", "", ["--this_argument_does_not_exists"])
        self.assertEqual(cm.exception.code, 1)

        with self.assertRaises(SystemExit) as cm:
            KeyringManager("", "", ["--select=not_a_number"])
        self.assertEqual(cm.exception.code, 1)
        KeyringManager("", "", ["--select=10"])

    def test_bdd_filename(self):
        # todo: add test for user pref filename override
        fake_filename1 = "fake_filename1"
        fake_filename2 = "fake_filename2"

        keyring_manager = KeyringManager("", fake_filename1, [])
        self.assertEqual(keyring_manager.filename, fake_filename1)

        keyring_manager = KeyringManager("", fake_filename1, ["--file=" + fake_filename2])
        self.assertEqual(keyring_manager.filename, fake_filename2)

    def _clean_bdd(self):
        if os.path.exists(self.bdd_filename):
            os.remove(self.bdd_filename)

    def _get_bdd(self):
        keyring_manager = KeyringManager("", self.bdd_filename, self.default_arguments + ["--get"])
        raw_bdd = keyring_manager.load_raw_bdd()
        return keyring_manager.parse_raw(raw_bdd)

    def test_command_get_empty(self):
        keyring_manager = KeyringManager("", self.bdd_filename, self.default_arguments + ["--get"])
        self.assertEqual(keyring_manager.command, "get")
        keyring_manager.run()
        bdd = self._get_bdd()
        self.assertEqual(len(bdd), 0)

    def test_command_add(self, new_pass="fake_pass", tags=["tag1", "tag2", "tag3"]):
        old_bdd = self._get_bdd()

        keyring_manager = KeyringManager("", self.bdd_filename, self.default_arguments + ["--add=" + new_pass] + tags)
        self.assertEqual(keyring_manager.command, "add")
        self.assertEqual(keyring_manager.key, new_pass)
        keyring_manager.run()
        bdd = self._get_bdd()
        self.assertEqual(len(bdd), len(old_bdd) + 1)

        decoded_bdd_entry = []
        for d in bdd[len(old_bdd)]:
            decoded_bdd_entry.append(d.decode('utf8'))
        self.assertEqual(decoded_bdd_entry, tags + [new_pass])

    def test_command_add_multiple(self):
        self.test_command_add("fake_pass_1", ["tag1", "tag2", "tag3"])
        self.test_command_add("fake_pass_2", ["tag1", "tag2", "tag4"])
        self.test_command_add("fake_pass_2", ["tag1", "tag5"])

    def test_command_get_select_multiple(self):
        self.test_command_add_multiple()
        keyring_manager = KeyringManager("", self.bdd_filename, self.default_arguments + ["--select=1"])
        self.assertEqual(keyring_manager.command, "get")
        self.assertEqual(keyring_manager.keyId, 1)
        keyring_manager.run()

        keyring_manager = KeyringManager("", self.bdd_filename, self.default_arguments + ["--get"])
        self.assertEqual(keyring_manager.command, "get")
        keyring_manager.run()

        keyring_manager = KeyringManager("", self.bdd_filename, self.default_arguments + ["--get", "tag1"]).run()
        keyring_manager = KeyringManager("", self.bdd_filename, self.default_arguments + ["--clip", "--get", "tag2"]).run()

    def _mocked_print(*args, **kwargs):
        pass

    @mock.patch('skrm.keyring_manager.KeyringManager.print_keyring', side_effect=_mocked_print)
    def test_command_search(self, mocked_print):
        self.test_command_add_multiple()

        keyring_manager = KeyringManager("", self.bdd_filename, self.default_arguments + ["--search", "tag1"])
        self.assertEqual(keyring_manager.command, "search")
        keyring_manager.run()
        self.assertEqual(mocked_print.call_count, 3)

        KeyringManager("", self.bdd_filename, self.default_arguments + ["--search", "tag2"]).run()
        self.assertEqual(mocked_print.call_count, 5)

        KeyringManager("", self.bdd_filename, self.default_arguments + ["--search", "tag5"]).run()
        self.assertEqual(mocked_print.call_count, 6)

    @mock.patch('skrm.keyring_manager.KeyringManager.print_keyring', side_effect=_mocked_print)
    def test_command_remove(self, mocked_print):
        self.test_command_add_multiple()

        keyring_manager = KeyringManager("", self.bdd_filename, self.default_arguments + ["--remove"])
        self.assertEqual(keyring_manager.command, "remove")
        with self.assertRaises(SystemExit) as cm:
            keyring_manager.run()
        self.assertEqual(cm.exception.code, 1)

        KeyringManager("", self.bdd_filename, self.default_arguments + ["--search", "tag2"]).run()
        self.assertEqual(mocked_print.call_count, 2)
        keyring_manager = KeyringManager("", self.bdd_filename, self.default_arguments + ["--select=1", "--remove"])
        self.assertEqual(keyring_manager.keyId, 1)
        keyring_manager.run()
        KeyringManager("", self.bdd_filename, self.default_arguments + ["--search", "tag2"]).run()
        self.assertEqual(mocked_print.call_count, 3)
        KeyringManager("", self.bdd_filename, self.default_arguments + ["--search", "tag4"]).run()
        self.assertEqual(mocked_print.call_count, 3)
        KeyringManager("", self.bdd_filename, self.default_arguments + ["--search", "tag3"]).run()
        self.assertEqual(mocked_print.call_count, 4)

    def test_command_update(self):
        self.test_command_add_multiple()

        new_key = "new_key"
        keyring_manager = KeyringManager("", self.bdd_filename, self.default_arguments + ["--update=" + new_key])
        self.assertEqual(keyring_manager.command, "update")
        self.assertEqual(keyring_manager.key, new_key)
        with self.assertRaises(SystemExit) as cm:
            keyring_manager.run()
        self.assertEqual(cm.exception.code, 1)

        old_bdd = self._get_bdd()
        self.assertNotEqual(old_bdd[1][-1].decode('utf8'), new_key)

        keyring_manager = KeyringManager("", self.bdd_filename, self.default_arguments + ["--select=1", "--update=" + new_key])
        self.assertEqual(keyring_manager.keyId, 1)
        keyring_manager.run()

        new_bdd = self._get_bdd()
        self.assertEqual(new_bdd[1][-1].decode('utf8'), new_key)

    def test_command_backup(self):
        self.test_command_add_multiple()

        backup_dest = "fake_dest"
        keyring_manager = KeyringManager("", self.bdd_filename, self.default_arguments + ["--backup=" + backup_dest])
        self.assertEqual(keyring_manager.command, "backup")
        self.assertEqual(keyring_manager.hostdest, backup_dest)

        with self.assertRaises(SystemExit) as cm:
            keyring_manager.run()
        self.assertEqual(cm.exception.code, 1)

