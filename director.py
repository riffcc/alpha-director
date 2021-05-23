#!/usr/bin/python3
# "a piece of knowledge, unlike a piece of physical property,
# can be shared by large groups of people without making anybody poorer."
# - Aaron Swartz
# In loving memory. This is for you.

# Import needed modules
from __future__ import with_statement
from pathlib import Path
from datetime import datetime
import ipfshttpclient
import os
import yaml
import json
import psycopg2.extras
import sys
import time  # i wish i could

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

# Get our Riff.CC credentials and load them in
sql_password = config["password"]
radio_folder = config["radio_folder"]
curator_user = config["curator_user"]
curator_pass = config["curator_pass"]
curator_host = config["curator_host"]
page_rows = int(config["page_rows"])

# Define methods


def setup_director():
    global cursor
    # TODO: move all this to def setup_director():
    # Connect to the Curator database
    connection = psycopg2.connect(host=curator_host,
                                  database="collection",
                                  user=curator_user,
                                  password=curator_pass)

    # create a cursor
    cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Open a read cursor
    # https://www.citusdata.com/blog/2016/03/30/five-ways-to-paginate/
    main_query = "DECLARE director_cur CURSOR FOR SELECT * FROM releases ORDER BY id;"
    cursor.execute(main_query)


def setup_timestamp():
    # Grab the current time UTC, then use it to create a fixed timestamp for this Director run/metadata set.
    current_time = datetime.now()
    formatted_timestamp = current_time.strftime("%Y%m%dT%H%M%SZ")
    return formatted_timestamp


def create_director_folder():
    global director_path
    director_path = radio_folder + "/director/" + director_timestamp
    try:
        os.makedirs(director_path, exist_ok=True)
    except:
        print("The Director folder @ " + director_path + " already exists. This SHOULD NEVER happen. Exiting.")
        sys.exit([150])


def create_subfolder(subfolder):
    create_releases_folder_path = director_path + "/" + subfolder
    print(create_releases_folder_path)
    try:
        os.makedirs(create_releases_folder_path, exist_ok=True)
    except:
        print("Tried to create " + create_releases_folder_path + " but did not succeed")
        sys.exit("COULD_NOT_CREATE_SUBFOLDER")


def fetch_data():
    global cursor
    # Grab the configured number of rows from The Curator's database
    fetch_query = "FETCH " + str(page_rows) + " FROM director_cur;"
    cursor.execute(fetch_query)
    fetched_data = cursor.fetchall()
    return fetched_data


def build_page_and_ids():
    global pageNum
    build_page_timer = time.perf_counter()
    # Increment the page number as we start a new one
    pageNum += 1
    print("Building page " + str(pageNum) + " as a group of " + str(page_rows) + " releases.")
    # Define a blank page list
    releases_list = []

    # For each release in the data we grabbed, build it and add it to the page's list
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
        release_id_dict["release_protocol"] = "ipfs"
        release_id_dict["release_id"] = release["id"]

        # Build the metadata dictionary from our data
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

        # Append additional data to our metadata so we can produce a more detailed "release_id" entry
        metadata_dict["source"] = release["source"]
        metadata_dict["description"] = release["description"]
        metadata_dict["mediainfo"] = release["mediainfo"]

        # Insert the completed metadata dictionary into the long form release
        release_id_dict["metadata"] = metadata_dict
        id_metadata_path = director_path + "/releases/release_id/" + str(release["id"]) + ".json"
        with open(id_metadata_path, 'w') as id_metadata_file:
            json.dump(release_id_dict, id_metadata_file)
        id_metadata_file.close()

    # Debug output
    print(releases_list)

    # Write out our completed page
    page_metadata_path = director_path + "/releases/pages/" + str(pageNum) + ".json"
    with open(page_metadata_path, 'w') as page_metadata_file:
        json.dump(releases_list, page_metadata_file)
    page_metadata_file.close()

    build_page_timer_done = time.perf_counter()
    return build_page_timer_done - build_page_timer


def build_all_pages():
    global result_set
    end_of_set = 0
    build_all_pages_timer = time.perf_counter()
    while not end_of_set:
        result_set = fetch_data()
        print("ROWS: " + str(cursor.rowcount))
        time_to_build_page = build_page_and_ids()
        print(f"Built page {pageNum} in {time_to_build_page:0.4f} seconds")
        if cursor.rowcount < page_rows:
            print("Reached the end, checking there are no more rows to fetch...")
            fetch_data()
            if cursor.rowcount == 0:
                print("Success.")
                end_of_set = 1
            else:
                die_message = "Something weird is going on, check The Curator."
                print(die_message)
                sys.exit(die_message)

    build_all_pages_timer_done = time.perf_counter()
    print(f"Built {pageNum} pages in {build_all_pages_timer_done - build_all_pages_timer:0.4f} seconds")


def add_to_ipfs(target_path):
    add_to_ipfs_timer = time.perf_counter()
    try:
        ipfs_added_path = ipfs_connection.add(target_path)
        add_to_ipfs_timer_done = time.perf_counter()
        print(f"Added {target_path} to IPFS in {add_to_ipfs_timer_done - add_to_ipfs_timer:0.4f} seconds")
        return ipfs_added_path[-1]['Hash']
    except Exception as e:
        print("Tried to add " + target_path + " to IPFS but there was an issue.")
        print(e)
        sys.exit("COULD_NOT_ADD_TO_IPFS")


def build_main_metadata():
    global releases_folder_ipfs_hash
    metadata_main_dict = {}
    releases_main_dict = {}
    available_apis = ["1.0.0"]

    metadata_main_dict["available_apis"] = available_apis
    metadata_main_dict["api_version"] = api_version
    releases_main_dict["pages"] = pageNum
    releases_main_dict["pages_folder"] = releases_folder_ipfs_hash
    releases_main_dict["release_id_folder"] = release_id_folder_ipfs_hash
    metadata_main_dict["releases"] = releases_main_dict
    # Print the completed metadata file for debugging
    print(json.dumps(metadata_main_dict))


# Connect to our local IPFS daemon
ipfs_connection = ipfshttpclient.connect()
# Create a timer so we can track how long tasks take
global_timer = time.perf_counter()
# Declare some empty and starting variables/objects.
pageNum = 0
cursor = ""
director_path = ""
# Statically set some variables
api_version = "1.0.0"  # We'll begin proper versioning once there's an app consuming the API

setup_director()
director_timestamp = setup_timestamp()
create_director_folder()
create_subfolder("releases/pages")
create_subfolder("releases/release_id")
build_all_pages()
print("Created " + str(pageNum) + " pages in folder " + director_path)
print("Adding the releases folder to IPFS.")

releases_folder_ipfs_hash = add_to_ipfs(director_path + "/releases/pages")
print(releases_folder_ipfs_hash)
print("Adding the release_id folder to IPFS.")
release_id_folder_ipfs_hash = add_to_ipfs(director_path + "/releases/release_id")
print(release_id_folder_ipfs_hash)
# build_featured_releases()
build_main_metadata()
# publish_to_bch_testnet()

# Calculate the total run time
global_timer_done = time.perf_counter()
print(f"The Director is finished. Transpilation and publication took {global_timer_done - global_timer:0.4f} seconds.")

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
