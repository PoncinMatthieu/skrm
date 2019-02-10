
import sys
import os

from .keyring_manager import KeyringManager


keyring_manager = KeyringManager(os.path.expanduser("~/.skrm/user.prefs"),
                                 os.path.expanduser("~/.skrm/bdd.gpg"),
                                 sys.argv[1:])
