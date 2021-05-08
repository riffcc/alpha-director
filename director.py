#!/usr/bin/python3
# "a piece of knowledge, unlike a piece of physical property, can be shared by large groups of people without making anybody poorer."
# - Aaron Swartz
# In loving memory. This is for you.
#
# The Director creates a JSON-based "pseudo-API" suitable for consumption by applications, both SPA and traditional.
# It is intended to create a package of metadata which can be stored entirely on IPFS and loaded as needed.
# Once the package is created, The Director uses a special custom SLP token to permanently record the root IPFS hash.
# Optionally, The Director can also sign the entire bundle to certify it, by simply signing the root IPFS hash.
#
# In order to provide a verifiable chain of trust, we propose a surprisingly simple solution.
#
# 1. Using the SLP standard, we create a custom for-purpose SLP token which can be used to provably certify metadata.
# 2. Two new wallets are created.
# 3. The SLP minting baton is used to mint tokens and send them to Wallet A.
# 4. Wallet A sends tokens to Wallet B, attaching the root IPFS hash as an OP_RETURN code.
#
# When the Riff.CC application starts, it simply checks Wallet B's transactions, finds the latest valid one
# and uses it to load in the root hash.
#
# To handle future updates, we simply publish a new IPFS hash by sending SLP tokens from Wallet A to Wallet B.
#
# This system allows us to create a special key pair that can be used to certify and publish content to Riff.CC,
# while retaining the ability to switch to a new keypair in the process. As all key pairs must have tokens generated
# by the minting baton in order to be considered valid, any key pair with tokens must have been created by Riff.CC.
#
# A compromised key pair could allow an attacker to publish content and force Riff.CC users to see it.
# However, it's possible to permanently invalidate a compromised key pair - we simply issue a new key pair, then update
# the Origin Root pointer to include the new Wallet B address instead of the old one.
#
# Upon starting, the Riff.CC application will fetch the Origin Root's JSON data, and check the SLP addresses
# it returns. If the suggested address' SLP tokens were received by its associated Wallet A at a later point in time
# than Wallet A in the old address received theirs, the new key pair ("metadataSigner") is more trustworthy than the
# currently stored address, and the currently stored address is discarded in favour of the new one.
#
# If the suggested address' SLP tokens are older than those of the currently selected key pair, we know that either a
# malicious attacker has altered the contents of the Origin Root gateway to return an old and compromised key pair,
# or - much more likely - the CDN is storing old or cached data. We simply ignore it and continue using the newer pair.
#
# In total this results in a system that allows for the issuing of new key pairs that can be distributed to less trusted
# parties due to the ease with which they can be revoked and made ineffective for attackers. The only known circumstance
# so far that allows for major attacks is if the Origin Root gateways are all down while a key is compromised,
# preventing us from making a new key pair take effect. Even in this circumstance, however, we could send a special
# "burn" transaction to the old Wallet B, with an OP_RETURN indicating that keypair has been burnt, followed by the
# next appropriate key pair to use. Seeing this, a client will switch to the new key pair without having to contact the
# Origin Root gateways.
#
# As this system helps facilitate a full and permanent switch to IPFS and the retirement of the BitTorrent protocol
# within the platform, it has a further advantage - as IPFS swarms are globally shared by default, any content we seed
# is provided to the rest of the IPFS ecosystem with no work required by us. This does potentially allow room for a
# competitor project to overtake and out-compete us, but in this event we have either failed in our mission or they are
# bringing interesting new ideas and passion to the space. In any case, most competitors will simply live alongside us
# and help boost the overall goals of both projects.
#
# Credits:
#  - https://stackoverflow.com/questions/10195139/how-to-retrieve-sql-result-column-value-using-column-name-in-python
#  - https://github.com/PyMySQL/PyMySQL

# Import needed modules
from __future__ import with_statement
from grizzled.os import working_directory
from urllib.parse import urlparse
import os, sys, yaml, re
import importlib

# Setup URL parser, thanks https://www.geeksforgeeks.org/python-check-url-string/
def ParseFindURLs(string):
    # findall() has been used
    # with valid conditions for urls in string
    regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
    url = re.findall(regex,string)
    return [x[0] for x in url]

# Set our API key
from pathlib import Path
apiname = os.path.expanduser('~/.rcc-api')
apitoken = Path(apiname).read_text()

# Dynamically load in our magic config files
configname = os.path.expanduser('~/.rcc-tools.yml')
config = yaml.safe_load(open(configname))

# Check if the config is empty
if config is None:
    print("Failed to load configuration.")
    sys.exit(1338)

# Get our Riff.CC credentials and load them in
rccuser = config["rccuser"]
rccpass = config["rccpass"]
sqlpassword = config["password"]

# Login to Riff.CC
# https://stackoverflow.com/questions/2910221/how-can-i-login-to-a-website-with-python

if(config["login"]):
    from twill.commands import *
    go('https://u.riff.cc/login')

    showforms()
    fv("1", "username", rccuser)
    fv("1", "password", rccpass)

    submit('0')

# Set our mysql password

import pymysql.cursors

# Connect to the database
connection = pymysql.connect(host='localhost',
                             user='unit3d',
                             password=sqlpassword,
                             database='unit3d',
                             cursorclass=pymysql.cursors.DictCursor)

with connection:
    with connection.cursor() as cursor:
        # Read a single record
        sql = "SELECT `id`, `description` FROM `torrents` WHERE seeders = 0"
        cursor.execute(sql)
        result_set = cursor.fetchall()
        for row in result_set:
            id = row["id"]
            print("Processing id "+ str(id))
            description = row["description"]
            # Grab our source from the description. Hopefully.
            # Set up some empty arrays
            urlLines = []
            actualURLs = []
            finalListOfURLs = []
            for line in description.splitlines():
                if "Source: [url]" in line:
                    print(line)
                    urlLines.append(line)
            for line in urlLines:
                # Sanitize the line
                line = line.replace('[url]', '')
                line = line.replace('[/url]', '')
                actualURLs.append(ParseFindURLs(line))

            # Go grab that torrent based on custom rules
            for actualURL in actualURLs:
                for actualActualURL in actualURL:
                    # Find the source of the torrent
                    sourceDomain = urlparse(actualActualURL).netloc
                    print(sourceDomain)
                    # Dynamically load in our magic config files
                    config = yaml.safe_load(open("rules/" + sourceDomain + ".yml"))
                    print(config["torrentregex"])
                    # Jump into the handler for that domain (thanks https://stackoverflow.com/questions/22955684/how-to-import-py-file-from-another-directory)
                    import importlib.machinery

                    moduleName = sourceDomain.replace('.', '')
                    loader = importlib.machinery.SourceFileLoader(moduleName, os.getcwd() + '/rules-py/' + moduleName + '.py')
                    lifehandler = loader.load_module(moduleName)

                    lifehandler.main(actualActualURL)

            # Fetch the torrent
            #go("https://u.riff.cc/torrents/download/" + str(id))
            #with working_directory("/tmp/torrents/"):
                #save_html(str(id) + ".torrent")
