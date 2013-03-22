#!/usr/bin/python

import os
import getopt
import sys
import subprocess
import re

def ExitUsage(error=0, msg=""):
    if error != 0:
        print("Error: " + msg)
    print("usage: ./skrm.py [OPTIONS] [COMMANDS] [TAGS]")
    print("skrm stands for simple keyring manager, it store keys with tags into a file encrypted using gpg.")
    print("skrm will ask for the master password to encrypt/decript the storing file.")
    print("OPTIONS:")
    print("\t-h, --help: Print usage.")
    print("\t-g, --get: Return keyrings matching strictly the given tags. This option is used by default. If a keyId is selected, a get or search return only the keyring matching the keyId.")
    print("\t-s, --search: Return keyrings matching the given tags (tags are interpreted as a regex expression).")
    print("\t-c, --clip: Copy the key of the last matched keyring from a get or a search into the clipboard using xclip. Nothing will be printed out to the shell.")
    print("COMMANDS:")
    print("\t--file=[FILENAME]: use the given file to read/store keyrings.")
    print("\t--recipient=[USER_ID_NAME]: set the user id name for gpg to get the key and encrypt the file.")
    print("\t--pass=[MASTER_PASS]: set the master pass to use when encrypting or decrypting the file.")
    print("\t--add=[KEY]: add a key to the file with the specified tags.")
    print("\t--select=[KEYID]: select a keyring using it's key id. To use with a command like \"remove\" or \"update\".")
    print("\t--remove: remove the selected key.")
    print("\t--update=[KEY]: update the selected key.")
    print("\t--backup=[HOSTDEST]: scp the bdd file to the given host destination.")
    print("TAGS:")
    print("\tA list of strings to define tags you want to use for any commands keyring related management.")
    sys.exit(error)

class KeyringManager:
    def __init__(self, argv):
        self.ReadUserPrefs()
        try:
            opts, args = getopt.getopt(argv, "hgsc", ["help", "file=", "get", "search", "pass=", "add=", "select=", "remove", "update=", "recipient=", "backup=", "clip"])
        except getopt.GetoptError:
            ExitUsage(1, "Bad arguments.")
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                ExitUsage()
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

    def ReadUserPrefs(self):
        self.userPrefFile = os.path.expanduser("~/.skrm/user.prefs")
        self.filename = os.path.expanduser("~/.skrm/bdd.gpg")
        self.command = "get"
        self.passphrase = ""
        self.tags = []
        self.key = ""
        self.keyId = -1
        self.recipient = ""
        self.clip = 0
        try:
            f = open(self.userPrefFile, "r")
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

    # decript gpg file and return the content
    def LoadRawBdd(self):
        args = ["gpg", "-dq"]
        if self.passphrase:
            args.append("--no-use-agent")
            args.append("--passphrase")
            args.append(self.passphrase)
        args.append(self.filename)
        #args = ["gpg", "-dq", "--no-use-agent", "--passphrase", self.passphrase, self.filename]
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

    def GetFonctor(self, keyring, tag):
        keyringLen = len(keyring)
        for i, t in enumerate(keyring):
            if i < (keyringLen - 1):
                if tag.upper() == t.upper():
                    return 1
        return 0

    def SearchFonctor(self, keyring, tag):
        keyringLen = len(keyring)
        p = re.compile(tag.upper())
        for i, t in enumerate(keyring):
            if i < (keyringLen - 1):
                if p.search(t.upper()) != None:
                    return 1
        return 0

    def PrintKeyring(self, i, keyring):
        if self.clip == 0: # print the keyring
            print(i),
            print(":"),
            print(keyring)
        else: # copy the keyring to the clipboard
            args = ["xclip"]
            p = subprocess.Popen(args, stdin = subprocess.PIPE)
            p.communicate(keyring[len(keyring) - 1])

    def PrintMatchingKeyrings(self, bdd, Functor):
        if self.keyId >= 0:
            print(self.keyId),
            print(":"),
            print(bdd[self.keyId])
        else:
            for i, keyring in enumerate(bdd):
                if len(self.tags) == 0:
                    print(i),
                    print(":"),
                    print(keyring)
                else:
                    foundAll = 1
                    for tag in self.tags:
                        if Functor(keyring, tag) == 0:
                            foundAll = 0
                    if foundAll == 1:
                        self.PrintKeyring(i, keyring)

    def CommandGet(self, bdd):
        print("GET")
        self.PrintMatchingKeyrings(bdd, self.GetFonctor)

    def CommandSearch(self, bdd):
        print("SEARCH")
        self.PrintMatchingKeyrings(bdd, self.SearchFonctor)

    def CommandAdd(self, bdd):
        newKeyring = self.tags
        newKeyring.append(self.key)
        bdd.append(newKeyring)
        self.SaveBdd(bdd)
        print("Add OK")

    def CommandRemove(self, bdd):
        if (self.keyId < 0 or self.keyId >= len(bdd)):
            print("Wrong argument, the given key id must be a valid number.")
            exit(-1)
        del bdd[self.keyId];
        self.SaveBdd(bdd)
        print("Remove OK")

    def CommandUpdate(self, bdd):
        if (self.keyId < 0 or self.keyId >= len(bdd)):
            print("Wrong argument, the given key id must be a valid number.")
            exit(-1)
        bdd[self.keyId][len(bdd[self.keyId]) - 1] = self.key;
        self.SaveBdd(bdd)
        print("Update OK")

    def CommandBackup(self):
        args = ["scp", self.filename, self.hostdest]
        p = subprocess.Popen(args, stdin = subprocess.PIPE, stderr = subprocess.PIPE, close_fds = True)
        stdout, stderr = p.communicate(None)
        stderr = stderr.rstrip()
        if stderr != "":
            print(stderr)
            print("Backup Failed!")
            exit(-1)
        print("Backup OK")

    def Exec(self):
        if self.command == "backup":
            self.CommandBackup()
        else:
            rawBdd = self.LoadRawBdd()
            bdd = self.ParseRaw(rawBdd)
            if self.command == "get":
                self.CommandGet(bdd)
            elif self.command == "search":
                self.CommandSearch(bdd)
            elif self.command == "add":
                self.CommandAdd(bdd)
            elif self.command == "remove":
                self.CommandRemove(bdd)
            elif self.command == "update":
                self.CommandUpdate(bdd)

if __name__=="__main__":
    keyringManager = KeyringManager(sys.argv[1:])
    keyringManager.Exec()
