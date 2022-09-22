#!/usr/bin/python3
# "a piece of knowledge, unlike a piece of physical property,
# can be shared by large groups of people without making anybody poorer."
# - Aaron Swartz
# In loving memory. This is for you.

# Import needed modules
from __future__ import with_statement
from pathlib import Path
from datetime import datetime
import os,sys,yaml,json
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
radio_folder = config["radio_folder"]
releases_per_page = config["releases_per_page"]
force_new_publication = config["force_new_publication"]

# Declare some empty and starting variables/objects.
total_number_of_releases = 0
build_tree_dict = {}
release_page_num = 1 # Page number is not zero indexed, so we start at 1.
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
    # Use the global version of variables we need to preserve between runs.
    global last_page_reached
    global release_page_num
    # Grab the configured number of rows from The Director's database
    if last_page_reached == False:
        # Fetch torrents
        release_page = requests.get(director_host + "api/torrents?page=" + str(release_page_num) + "&api_token=" + api_token).json()
        # If this is the first page we're retrieving, print the number of rows per query.
        if(release_page_num == 1):
            print("Fetching " + str(release_page["meta"]["per_page"]) + " rows at a time, to build pages of size " + str(releases_per_page))
        # Check if we have reached the last page
        if(release_page["meta"]["current_page"] == release_page["meta"]["last_page"]):
            last_page_reached = True
            print("Reached the last page.")
        else:
            # Increment page number by 1.
            release_page_num += 1    
        fetched_data = release_page["data"]
        return fetched_data


def build_all_pages():
    # Load needed variables as globals.
    global build_tree_dict
    global total_number_of_releases
    global category_metadata_tree

    # Put some initial variables into place in the build tree.
    build_tree_dict["releases_pages"] = 0
    build_tree_dict["releases_release_counter"] = 0
    build_tree_dict["featured_pages"] = 0
    build_tree_dict["featured_release_counter"] = 0
    build_tree_dict["featured_category_data"] = {}

    while last_page_reached == False:
        print("Fetching data from The Director...")
        result_set = fetch_data()
        for release in result_set:
            # Create empty dictionaries for the release and for the metadata contained inside it
            release_dict = {}
            release_id_dict = {}
            metadata_dict = {}
            # No-op to silence PyCharm warnings
            pass
            # Begin building the release_dict from our data
            release_dict["release_protocol"] = "ipfs"
            release_dict["release_id"] = release["id"]
            release_dict["name"] = release["attributes"]["name"]
            release_id_dict["release_protocol"] = "ipfs"
            release_id_dict["release_id"] = release["id"]
            release_id_dict["name"] = release["attributes"]["name"]

            # Extract the description
            release_info = (json.loads(release["attributes"]["description"]))

            # Build the metadata dictionary from our data
            metadata_dict["hashes"] = {}

            # Main data hashes
            # We require the IPFS hash of the content at minimum
            metadata_dict["hashes"]["content"] = release_info["hashes"]["content"]
            # Optional extra data
            if "hint" in release_info["hashes"]:
                metadata_dict["hashes"]["hint"] = release_info["hashes"]["hint"]
            if "thumbnail" in release_info["hashes"]:
                metadata_dict["hashes"]["thumbnail"] = release_info["hashes"]["thumbnail"]
            if "poster" in release_info["hashes"]:
                metadata_dict["hashes"]["poster"] = release_info["hashes"]["poster"]
            
            metadata_dict["uploader"] = release["attributes"]["uploader"]
            metadata_dict["category"] = release["attributes"]["category"]
            metadata_dict["type"] = release["attributes"]["type"]
            metadata_dict["resolution"] = release["attributes"]["resolution"]
            if "codec" in release_info:
                metadata_dict["codec"] = release_info["codec"]
            metadata_dict["number_of_files"] = release["attributes"]["num_file"]
            if release["attributes"]["tmdb_id"] != 0:
                metadata_dict["tmdb_id"] = release["attributes"]["tmdb_id"]
            if release["attributes"]["tmdb_id"] != 0:
                metadata_dict["tmdb_id"] = release["attributes"]["tmdb_id"]
            

            # If instructed, insert a random string into our metadata as we build it so we can benchmark Director.
            if force_new_publication == 1:
                metadata_dict["salt"] = str(os.urandom(128))

            # Insert the complete metadata dictionary into our release
            release_dict["metadata"] = metadata_dict

        print(release_dict)

print("Welcome to Riff.CC. Let's free the world's culture - again.")
print("The Director will create a metadata tree and publish it to IPFS.")
if force_new_publication == True:
    print("Special mode activated - will force IPFS to rehash everything as we build this.")
director_timestamp = setup_timestamp()

# Set up directory structure
create_director_folder()
create_subfolder("releases/pages")
create_subfolder("releases/release_id")
create_subfolder("featured/pages")

# Build pages
build_all_pages()
