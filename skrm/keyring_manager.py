
from __future__ import print_function
import os
import getopt
import sys
import subprocess
import re


def exit_with_usage(error=0, msg=""):
    if error != 0:
        print("Error: " + msg)
    print("usage: ./skrm [OPTIONS] [COMMANDS] [TAGS]")
    print("skrm stands for simple keyring manager, it stores keys with tags into a file encrypted using gpg.")
    print("skrm will ask for the master password to encrypt/decrypt the storing file.")
    print("OPTIONS:")
    print("\t-h, --help: Print usage.")
    print("\t-g, --get: Return keyrings matching strictly the given tags. This option is used by default. If a keyId is selected, a get or a search return only the keyring matching the keyId.")
    print("\t-s, --search: Return keyrings matching the given tags (tags are interpreted as a regex expression).")
    print("\t-c, --clip: Copy the key of the last matched keyring from a get or a search into the clipboard using xclip. Nothing will be printed out to the shell.")
    print("COMMANDS:")
    print("\t--file=[FILENAME]: use the given file to read/store keyrings.")
    print("\t--recipient=[USER_ID_NAME]: set the user id name for gpg to get the key and encrypt the file.")
    print("\t--pass=[MASTER_PASS]: set the master pass to use when encrypting or decrypting the file.")
    print("\t--add=[KEY]: add a key to the file with the specified tags.")
    print("\t--select=[KEYID]: select a keyring using its key id. To use with a command like \"remove\" or \"update\".")
    print("\t--remove: remove the selected key.")
    print("\t--update=[KEY]: update the selected key.")
    print("\t--backup=[HOSTDEST]: scp the bdd file to the given host destination.")
    print("TAGS:")
    print("\tA list of strings to define tags you want to use for any commands keyring related management.")
    sys.exit(error)


class KeyringManager:
    def __init__(self, user_pref_path, bdd_path, argv):
        self.read_user_prefs(user_pref_path, bdd_path)
        try:
            opts, args = getopt.getopt(argv, "hgsc", ["help", "file=", "get", "search", "pass=", "add=", "select=", "remove", "update=", "recipient=", "backup=", "clip"])
        except getopt.GetoptError:
            exit_with_usage(1, "Bad arguments.")
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                exit_with_usage()
            elif opt == "--file":
                self.filename = os.path.expanduser(arg)
            elif opt in ("-g", "--get"):
                self.command = "get"
            elif opt in ("-s", "--search"):
                self.command = "search"
            elif opt == "--add":
                self.command = "add"
                self.key = arg
            elif opt == "--select":
                if arg.isdigit():
                    self.keyId = int(arg)
                else:
                    exit_with_usage(1, "The given keyid is not a number.")
            elif opt == "--remove":
                self.command = "remove"
            elif opt == "--update":
                self.command = "update"
                self.key = arg
            elif opt == "--pass":
                self.passphrase = arg
            elif opt == "--recipient":
                self.recipient = arg
            elif opt == "--backup":
                self.command = "backup"
                self.hostdest = arg
            elif opt in ("-c", "--clip"):
                self.clip = 1
        for arg in args:
            self.tags.append(arg)

    def read_user_prefs(self, user_pref_path, bdd_path):
        user_pref_file = user_pref_path
        self.filename = bdd_path
        self.command = "get"
        self.passphrase = ""
        self.tags = []
        self.key = ""
        self.keyId = -1
        self.recipient = ""
        self.clip = 0
        try:
            with open(user_pref_file, "r") as f:
                for line in f:
                    option = line.split("=")
                    option[1] = option[1].rstrip('\n')
                    if option[0][0] != '#':
                        if option[0] == "file":
                            self.filename = option[1]
                        elif option[0] == "recipient":
                            self.recipient = option[1]
        except IOError: # use preffs not found, do nothing. args must be defined in command line arguments.
            pass

    def load_raw_bdd(self):
        """ Decript gpg file and return the content """
        args = ["gpg", "-dq"]
        if self.passphrase:
            args.append("--no-use-agent")
            args.append("--passphrase")
            args.append(self.passphrase)
        args.append(self.filename)
        p = subprocess.Popen(args, stdin = subprocess.PIPE, stdout = subprocess.PIPE, stderr = subprocess.PIPE, close_fds = True)
        stdout, stderr = p.communicate(None)
        if stdout == "" and stdout != "":
            print(stderr)
            exit(1)
        return stdout.rstrip()

    def save_raw_bdd(self, raw):
        """ Encript gpg file """
        args = ["gpg", "--yes", "-e", "-r", self.recipient, "-o", self.filename]
        p = subprocess.Popen(args, stdin = subprocess.PIPE, stdout = subprocess.PIPE, stderr = subprocess.PIPE, close_fds = True)
        stdout, stderr = p.communicate(raw)
        stdout = stdout.rstrip()
        stderr = stderr.rstrip()
        if stdout != "":
            print(stdout)
        if stderr != "":
            print(stderr)

    def parse_raw(self, raw):
        bdd = []
        if raw:
            keyrings = raw.split(b"\x03")
            for keyring in keyrings:
                bdd.append(keyring.split(b"\x02"))
        return bdd

    def parse_bdd(self, bdd):
        raw = b""
        bddLen = len(bdd)
        for i, keyring in enumerate(bdd):
            keyringLen = len(keyring)
            for j, tag in enumerate(keyring):
                if isinstance(tag, str):
                    tag = bytes(tag, 'utf8')
                raw += tag
                if j < (keyringLen - 1):
                    raw += b"\x02"
            if i < (bddLen - 1):
                raw += b"\x03"
        return raw

    def save_bdd(self, bdd):
        raw = self.parse_bdd(bdd)
        self.save_raw_bdd(raw)

    def get_fonctor(self, keyring, tag):
        keyringLen = len(keyring)
        for i, t in enumerate(keyring):
            if i < (keyringLen - 1):
                if tag.upper() == t.upper().decode('utf8'):
                    return 1
        return 0

    def search_fonctor(self, keyring, tag):
        keyringLen = len(keyring)
        p = re.compile(tag.upper())
        for i, t in enumerate(keyring):
            if i < (keyringLen - 1):
                if p.search(t.upper().decode('utf8')) != None:
                    return 1
        return 0

    def print_keyring(self, i, keyring):
        if self.clip == 0: # print the keyring
            print(i, end='')
            print(":", end='')
            print(keyring)
        else: # copy the keyring to the clipboard
            from sys import platform as _platform
            if _platform == "linux" or _platform == "linux2": # linux
                args = ["xclip"]
                p = subprocess.Popen(args, stdin = subprocess.PIPE)
                p.communicate(keyring[len(keyring) - 1])
            elif _platform == "darwin": # OS X
                args = ["pbcopy"]
                p = subprocess.Popen(args, stdin = subprocess.PIPE)
                p.communicate(keyring[len(keyring) - 1])
            elif _platform == "win32": # Windows
                print("Can't copy on clipboard under windows, method not implemented!")

    def print_matching_keyrings(self, bdd, Functor):
        if self.keyId >= 0:
            print(self.keyId, end='')
            print(":", end='')
            print(bdd[self.keyId])
        else:
            for i, keyring in enumerate(bdd):
                if len(self.tags) == 0:
                    print(i, end='')
                    print(":", end='')
                    print(keyring)
                else:
                    foundAll = 1
                    for tag in self.tags:
                        if Functor(keyring, tag) == 0:
                            foundAll = 0
                    if foundAll == 1:
                        self.print_keyring(i, keyring)

    def command_get(self, bdd):
        print("GET")
        self.print_matching_keyrings(bdd, self.get_fonctor)

    def command_search(self, bdd):
        print("SEARCH")
        self.print_matching_keyrings(bdd, self.search_fonctor)

    def command_add(self, bdd):
        newKeyring = self.tags
        newKeyring.append(self.key)
        bdd.append(newKeyring)
        self.save_bdd(bdd)
        print("Add OK")

    def command_remove(self, bdd):
        if (self.keyId < 0 or self.keyId >= len(bdd)):
            exit_with_usage(1, "Wrong argument, the given key id must be a valid number.")
        print("Removing: ", end='')
        print(bdd[self.keyId])
        del bdd[self.keyId];
        self.save_bdd(bdd)
        print("Remove OK")

    def command_update(self, bdd):
        if (self.keyId < 0 or self.keyId >= len(bdd)):
            exit_with_usage(1, "Wrong argument, the given key id must be a valid number.")
        bdd[self.keyId][len(bdd[self.keyId]) - 1] = self.key;
        print("New keyring: ", end='')
        print(bdd[self.keyId])
        self.save_bdd(bdd)
        print("Update OK")

    def command_backup(self):
        args = ["scp", self.filename, self.hostdest]
        p = subprocess.Popen(args, stdin = subprocess.PIPE, stderr = subprocess.PIPE, close_fds = True)
        stdout, stderr = p.communicate(None)
        stderr = stderr.rstrip()
        if stderr != "":
            print(stderr)
            print("Backup Failed!")
            exit(1)
        print("Backup OK")

    def run(self):
        if self.command == "backup":
            self.command_backup()
        else:
            raw_bdd = self.load_raw_bdd()
            bdd = self.parse_raw(raw_bdd)
            if self.command == "get":
                self.command_get(bdd)
            elif self.command == "search":
                self.command_search(bdd)
            elif self.command == "add":
                self.command_add(bdd)
            elif self.command == "remove":
                self.command_remove(bdd)
            elif self.command == "update":
                self.command_update(bdd)
