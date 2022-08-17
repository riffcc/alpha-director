#!/usr/bin/python3
# "a piece of knowledge, unlike a piece of physical property,
# can be shared by large groups of people without making anybody poorer."
# - Aaron Swartz
# In loving memory. This is for you.

# Import needed modules
from __future__ import with_statement
from pathlib import Path
from datetime import datetime
import os,sys,yaml
import requests

# Set our API key
api_name = os.path.expanduser('~/.rcc-api')
api_token = Path(api_name).read_text()

# Dynamically load in our magic config files
config_name = os.path.expanduser('~/.rcc-tools.yml')
config = yaml.safe_load(open(config_name))

# Check if the config is empty
if config is None:
    print("Failed to load configuration.")
    sys.exit(1338)

# Load Director config vars
director_host = config["director_host"]
force_new_publication = config["force_new_publication"]
radio_folder = config["radio_folder"]

# Declare some empty and starting variables/objects.
total_number_of_releases = 0
build_tree_dict = {}
torrent_page_num = 1 # Page number is not zero indexed, so we start at 1.
last_page_reached = False

# Statically set some variables
api_version = "0.1.0"  # We'll begin proper versioning once there's an app consuming the API


def setup_timestamp():
    # Grab the current time UTC, then use it to create a fixed timestamp for this Director run/metadata set.
    current_time = datetime.now()
    formatted_timestamp = current_time.strftime("%Y%m%dT%H%M%SZ")
    return formatted_timestamp


def create_director_folder():
    global director_path
    director_path = radio_folder + "/director/" + director_timestamp
    symlink_path = radio_folder + "/director/latest"
    symlink_path_temp = radio_folder + "/director/latest_new"

    try:
        os.makedirs(director_path, exist_ok=True)
        os.symlink(director_path, symlink_path_temp)
        os.replace(symlink_path_temp, symlink_path)
    except:
        print("The Director folder @ " + director_path + " already exists. This SHOULD NEVER happen. Exiting.")
        sys.exit([150])


def create_subfolder(subfolder):
    create_releases_folder_path = director_path + "/" + subfolder
    try:
        os.makedirs(create_releases_folder_path, exist_ok=True)
    except:
        print("Tried to create " + create_releases_folder_path + " but did not succeed")
        sys.exit("COULD_NOT_CREATE_SUBFOLDER")


def fetch_data():
    # Grab the configured number of rows from The Curator's database
    if last_page_reached == False:
        # Fetch torrents
        release_page = requests.get(director_host + "api/torrents?api_token=" + api_token).json()
        for release in release_page["data"]:
            print(release)
        sys.exit("Exiting...")
        return fetched_data

print("Welcome to Riff.CC. Let's free the world's culture - again.")
print("The Director will create a metadata tree and publish it to IPFS.")
if force_new_publication == True:
    print("Special mode activated - will force IPFS to rehash everything as we build this.")
director_timestamp = setup_timestamp()

fetch_data()