#!/usr/bin/python3
# "a piece of knowledge, unlike a piece of physical property,
# can be shared by large groups of people without making anybody poorer."
# - Aaron Swartz
# In loving memory. This is for you.

# Import needed modules
from __future__ import with_statement
from pathlib import Path
import os
import yaml
import json
import psycopg2.extras
import sys

# Define methods


def build_pages():
    print("Building page " + str(pageNum) + " as a group of " + str(page_rows) + " releases.")
    # Grab the configured number of rows from The Curator's database
    fetchquery = "FETCH " + str(page_rows) + " FROM director_cur;"
    cursorpg.execute(fetchquery)
    result_set = cursorpg.fetchall()

    # Define a blank page list
    releases_list = []

    # For each release in the data we grabbed, build it and add it to the page's list
    for release in result_set:
        # Statically define the release protocol (for now)
        release_protocol = "ipfs"
        # Use the data we grabbed to populate some normal Python variables (likely some better way to do this)
        release_id = release["id"]
        name = release["name"]
        ipfs_hash = release["ipfs_hash"]
        creator = release["creator"]
        publication_date = release["publication_date"]
        category = release["category_id"]
        release_type = release["type_id"]
        resolution = release["resolution_id"]
        uploader = release["uploader_id"]
        featured = release["featured"]
        created_at = release["created_at"]
        updated_at = release["updated_at"]
        tags = release["tags"]
        cover = release["cover"]
        licence = release["licence"]
        subtitles = release["subtitles"]
        subtitles_file = release["subtitles_file"]

        # Create empty dictionaries for the release and for the metadata contained inside it
        release_dict = {}
        metadata_dict = {}
        # No-op to silence PyCharm warnings
        pass
        # Begin building the release_dict from our variables
        release_dict["release_protocol"] = release_protocol
        release_dict["release_id"] = release_id

        # Create our metadata from the variables defined earlier
        for dict_item in ["name", "ipfs_hash", "creator"]:
            metadata_dict[dict_item] = eval(dict_item)

        # Insert the complete metadata dictionary into our release
        release_dict["metadata"] = metadata_dict

        # Take the completed release and append it to the releases_list
        releases_list.append(release_dict.copy())

    print(releases_list)

    # Write out our completed page
    with open('/opt/radio/test/output.json', 'w') as outfile:
        json.dump(releases_list, outfile)
    outfile.close()


def build_item():
    print("DEBUG: This method will build the item later but for now is a stub")

# Set our API key
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
sqlpassword = config["password"]
curator_user = config["curator_user"]
curator_pass = config["curator_pass"]
curator_host = config["curator_host"]
page_rows = config["page_rows"]

# Connect to the Curator database
connpg = psycopg2.connect(host=curator_host,
                          database="collection",
                          user=curator_user,
                          password=curator_pass)

# create a cursor
cursorpg = connpg.cursor(cursor_factory=psycopg2.extras.DictCursor)

# Open a read cursor
# https://www.citusdata.com/blog/2016/03/30/five-ways-to-paginate/
mainquery = "DECLARE director_cur CURSOR FOR SELECT * FROM releases ORDER BY id;"
cursorpg.execute(mainquery)

pageNum = 0




# TODOs: (things the script does not do yet)
# verification (optional)
# shell out to Sentinel and Janitor to validate data
# build the main releases files
# build the featured files
# build the featured categories
# build the deleted IDs and hashes
# pull relationships from the Curator
# build the related relationships for releases
# build the related relationships for artists
#
# Developer notes:
# While we could cast category_ids etc to actual categories within The Director,
# it makes more sense to have them defined in the database and built as a separate bit of metadata_ids in the metadata.
# This allows for dynamism, and we can also fairly trivially cast them to "actual types" later, or even do both at once.
# During debugging we may simply do both at once, then drop the "actual types" to keep metadata lighter.
