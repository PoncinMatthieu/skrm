#!/usr/bin/python

import os
import getopt
import sys
import subprocess

def ExitUsage(error=0, msg=""):
    if error != 0:
        print("Error: " + msg)
    print("usage: ./skrm.py [OPTIONS] [COMMANDS]")
    print("skrm stands for simple keyring manager, it store keys with tags into a file encrypted using gpg.")
    print("skrm will ask for the master password to encrypt/decript the storing file.")
    print("OPTIONS:")
    print("\t-h, --help: print usage.")
    print("COMMANDS:")
    print("\t--file=[FILENAME]: use the given file to read/store keyrings.")
    print("\t--recipient=[USER_ID_NAME]: set the user id name for gpg to get the key and encrypt the file.")
    print("\t--pass=[MASTER_PASS]: set the master pass to use when encrypting or decrypting the file.")
    print("\t--get: the option is used by default. Return keys matching the specified tags.")
    print("\t--tags=[TAG1:TAG2:TAG3]: set a list of tag to search or to set.")
    print("\t--add=[KEY]: add a key to the file with the specified tags.")
    print("\t--remove=[KEYID]: remove the key using the key id.")
    sys.exit(error)

class KeyringManager:
    def __init__(self, argv):
        self.ReadUserPrefs()
        try:
            opts, args = getopt.getopt(argv, "h", ["help", "file=", "get", "pass=", "add=", "tags=", "remove=", "recipient="])
        except getopt.GetoptError:
            ExitUsage(1, "Bad arguments.")
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                ExitUsage()
            elif opt == "--file":
                self.filename = os.path.expanduser(arg)
            elif opt == "--tags":
                listTag = arg.split(":")
                for tag in listTag:
                    self.tags.append(tag)
            elif opt == "--get":
                self.command = "get"
            elif opt == "--add":
                self.command = "add"
                self.key = arg
            elif opt == "--remove":
                self.command = "remove"
                self.key = arg
            elif opt == "--pass":
                self.passphrase = arg
            elif opt == "--recipient":
                self.recipient = arg

    def ReadUserPrefs(self):
        self.userPrefFile = os.path.expanduser("~/.skrm/user.prefs")
        self.filename = os.path.expanduser("~/.skrm/bdd.gpg")
        self.command = "get"
        self.passphrase = "";
        self.tags = []
        self.key = ""
        self.recipient = ""
        f = open(self.userPrefFile, "r")
        for line in f:
            option = line.split("=")
            option[1] = option[1].rstrip('\n')
            if option[0][0] != '#':
                if option[0] == "file":
                    self.filename = option[1]
                elif option[0] == "recipient":
                    self.recipient = option[1]

    # decript gpg file and return the content
    def LoadRawBdd(self):
        args = ["gpg", "-dq", "--no-use-agent", "--passphrase", self.passphrase, self.filename]
        p = subprocess.Popen(args, stdin = subprocess.PIPE, stdout = subprocess.PIPE, stderr = subprocess.PIPE, close_fds = True)
        stdout, stderr = p.communicate(None)
        if stdout == "" and stdout != "":
            print(stderr)
            exit(-1)
        return stdout.rstrip()

    # encript gpg file
    def SaveRawBdd(self, raw):
        args = ["gpg", "-e", "-r", self.recipient, "-o", self.filename]
        p = subprocess.Popen(args, stdin = subprocess.PIPE, stdout = subprocess.PIPE, stderr = subprocess.PIPE, close_fds = True)
        stdout, stderr = p.communicate(raw)
        stdout = stdout.rstrip()
        stderr = stderr.rstrip()
        if stdout != "":
            print(stdout)
        if stderr != "":
            print(stderr)

    def ParseRaw(self, raw):
        bdd = []
        if raw:
            keyrings = raw.split("\x03")
            for keyring in keyrings:
                bdd.append(keyring.split("\x02"))
        return bdd

    def ParseBdd(self, bdd):
        raw = ""
        bddLen = len(bdd)
        for i, keyring in enumerate(bdd):
            keyringLen = len(keyring)
            for j, tag in enumerate(keyring):
                raw += tag
                if j < (keyringLen - 1):
                    raw += "\x02"
            if i < (bddLen - 1):
                raw += "\x03"
        return raw

    def SaveBdd(self, bdd):
        raw = self.ParseBdd(bdd)
        self.SaveRawBdd(raw)

    def CommandGet(self, bdd):
        print("GET")
        for i, keyring in enumerate(bdd):
            if len(self.tags) == 0:
                print(i),
                print(":"),
                print(keyring)
            else:
                foundAll = 1
                for tag in self.tags:
                    found = 0
                    for t in keyring:
                        if tag.upper() == t.upper():
                            found = 1
                    if found == 0:
                        foundAll = 0
                if foundAll == 1:
                    print(i),
                    print(":"),
                    print(keyring)

    def CommandAdd(self, bdd):
        newKeyring = self.tags
        newKeyring.append(self.key)
        bdd.append(newKeyring)
        self.SaveBdd(bdd)
        print("Add OK")

    def CommandRemove(self, bdd):
        del bdd[int(self.key)];
        self.SaveBdd(bdd)
        print("Remove OK")

    def Exec(self):
        rawBdd = self.LoadRawBdd()
        bdd = self.ParseRaw(rawBdd)
        if self.command == "get":
            self.CommandGet(bdd)
        elif self.command == "add":
            self.CommandAdd(bdd)
        elif self.command == "remove":
            self.CommandRemove(bdd)


keyringManager = KeyringManager(sys.argv[1:])
keyringManager.Exec()
