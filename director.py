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
from datetime import datetime

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
radio_folder = config["radio_folder"]
curator_user = config["curator_user"]
curator_pass = config["curator_pass"]
curator_host = config["curator_host"]
page_rows = config["page_rows"]

# Define methods


def setup_director():
    global cursorpg
    # TODO: move all this to def setup_director():
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


def setup_timestamp():
    # Grab the current time UTC, then use it to create a fixed timestamp for this Director run/metadata set.
    current_time = datetime.now()
    formatted_timestamp = current_time.strftime("%Y%m%dT%H%M%SZ")
    return formatted_timestamp


def create_director_folder():
    director_path = radio_folder + "/director/" + director_timestamp
    try:
        os.makedirs(director_path, exist_ok=True)
    except:
        print("The Director folder @ " + director_path + " already exists. This SHOULD NEVER happen. Exiting.")
        sys.exit([150])


def fetch_data():
    global cursorpg
    # Grab the configured number of rows from The Curator's database
    fetchquery = "FETCH " + str(page_rows) + " FROM director_cur;"
    cursorpg.execute(fetchquery)
    fetched_data = cursorpg.fetchall()
    return fetched_data


def build_page():
    print("Building page " + str(pageNum) + " as a group of " + str(page_rows) + " releases.")
    # Define a blank page list
    releases_list = []

    # For each release in the data we grabbed, build it and add it to the page's list
    for release in result_set:
        # Statically define the release protocol (for now)
        release_protocol = "ipfs"
        # Create empty dictionaries for the release and for the metadata contained inside it
        release_dict = {}
        metadata_dict = {}
        # No-op to silence PyCharm warnings
        pass
        # Begin building the release_dict from our data
        release_dict["release_protocol"] = "ipfs"
        release_dict["release_id"] = release["id"]

        # Build the metadata dictionary from our data
        # TODO - surely we can just do this for everything except "id" in the DB columns?
        metadata_dict["name"] = release["name"]
        metadata_dict["ipfs_hash"] = release["ipfs_hash"]
        metadata_dict["creator"] = release["creator"]
        metadata_dict["publication_date"] = str(release["publication_date"])
        metadata_dict["category"] = release["category_id"]
        metadata_dict["release_type"] = release["type_id"]
        metadata_dict["resolution"] = release["resolution_id"]
        metadata_dict["uploader"] = release["uploader_id"]
        metadata_dict["featured"] = release["featured"]
        metadata_dict["created_at"] = str(release["created_at"])
        metadata_dict["updated_at"] = str(release["updated_at"])
        metadata_dict["tags"] = release["tags"]
        metadata_dict["cover"] = release["cover"]
        metadata_dict["licence"] = release["licence"]
        metadata_dict["subtitles"] = release["subtitles"]
        metadata_dict["subtitles_file"] = release["subtitles_file"]

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

# Declare some empty and starting variables/objects.
pageNum = 0
cursorpg = ""

setup_director()
director_timestamp = setup_timestamp()
create_director_folder()
result_set = fetch_data()
build_page()
print()

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
