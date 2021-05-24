#!/usr/bin/python3
# "a piece of knowledge, unlike a piece of physical property,
# can be shared by large groups of people without making anybody poorer."
# - Aaron Swartz
# In loving memory. This is for you.

# Uses a lot of duplicate code, urgently needs some refactoring once core functionality is there.

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
query_rows = int(config["page_rows"])
force_new_publication = int(config["force_new_publication"])

# Define methods


def setup_cursor(query):
    global cursor
    # Connect to the Curator database
    connection = psycopg2.connect(host=curator_host,
                                  database="collection",
                                  user=curator_user,
                                  password=curator_pass)

    # create a cursor
    cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Open a read cursor
    # https://www.citusdata.com/blog/2016/03/30/five-ways-to-paginate/
    cursor.execute(query)


def destroy_cursor():
    global cursor
    kill_query = "COMMIT;"
    cursor.execute(kill_query)


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
    global cursor
    # Grab the configured number of rows from The Curator's database
    fetch_query = "FETCH " + str(query_rows) + " FROM director_cur;"
    cursor.execute(fetch_query)
    fetched_data = cursor.fetchall()
    return fetched_data


def build_all_pages():
    global result_set
    global build_tree_dict
    global total_number_of_releases
    build_tree_dict["releases_pages"] = 0
    build_tree_dict["releases_release_counter"] = 0
    build_tree_dict["featured_pages"] = 0
    build_tree_dict["featured_release_counter"] = 0
    build_tree_dict["featured_category_data"] = {}

    # TODO: build a list of category IDs here from the database
    # for now we'll do it statically which is silly af
    # also this probably isn't the right place to do this anyways wheeeeeee
    category_id_list = []
    for i in range(10):
        category_id_list.append(str(i))
    category_id_list.append("1337")
    build_tree_dict["featured_categories"] = category_id_list

    total_pages_num = 0
    end_of_set = 0
    build_all_pages_timer = time.perf_counter()
    # TODO - move these into build_tree_dict
    releases_page_release_list = []
    featured_page_release_list = []

    for featured_category in build_tree_dict["featured_categories"]:
        # Build our data structures before we use them
        build_tree_dict["featured_category_data"][str(featured_category)] = {}
        build_tree_dict["featured_category_data"][str(featured_category)]["category_release_list"] = []
        build_tree_dict["featured_category_data"][str(featured_category)]["category_pages"] = 0
        build_tree_dict["featured_category_data"][str(featured_category)]["category_release_counter"] = 0
        create_subfolder("featured/category/" + featured_category + "/pages/")

    print("Fetching data from the Curator.")
    while not end_of_set:
        result_set = fetch_data()
        print("Fetching...")
        # For each release in the data we grabbed, process it
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
            metadata_dict["category_id"] = release["category_id"]
            metadata_dict["release_type"] = release["type_id"]
            metadata_dict["resolution_id"] = release["resolution_id"]
            metadata_dict["uploader_id"] = release["uploader_id"]
            metadata_dict["featured"] = release["featured"]
            metadata_dict["created_at"] = str(release["created_at"])
            metadata_dict["updated_at"] = str(release["updated_at"])
            metadata_dict["tags"] = release["tags"]
            metadata_dict["cover"] = release["cover"]
            metadata_dict["licence"] = release["licence"]
            metadata_dict["subtitles"] = release["subtitles"]
            metadata_dict["subtitles_file"] = release["subtitles_file"]

            # If instructed, insert a random string into our metadata as we build it so we can benchmark Director.
            if force_new_publication == 1:
                metadata_dict["salt"] = str(os.urandom(128))

            # Insert the complete metadata dictionary into our release
            release_dict["metadata"] = metadata_dict

            # Take the completed release and append it to the releases_page_release_list
            releases_page_release_list.append(release_dict.copy())
            build_tree_dict["releases_release_counter"] += 1

            # Increment our counter (TODO: just check how many valid rows are in the DB instead)
            total_number_of_releases += 1

            # If this is a featured release, add it to featured releases and any categories it's in
            if release["featured"]:
                featured_page_release_list.append(release_dict.copy())
                build_tree_dict["featured_release_counter"] += 1
                # Add it to whichever category is appropriate
                build_tree_dict["featured_category_data"][str(release["category_id"])]["category_release_list"].append(release_dict.copy())
                build_tree_dict["featured_category_data"][str(release["category_id"])]["category_release_counter"] += 1

            # Append additional data to our metadata so we can produce a more detailed "release_id" entry
            metadata_dict["source"] = release["source"]
            metadata_dict["description"] = release["description"]
            metadata_dict["mediainfo"] = release["mediainfo"]

            # Insert the completed metadata dictionary into the long form releases
            release_id_dict["metadata"] = metadata_dict
            id_metadata_path = director_path + "/releases/release_id/" + str(release["id"]) + ".json"
            with open(id_metadata_path, 'w') as id_metadata_file:
                json.dump(release_id_dict, id_metadata_file)
            id_metadata_file.close()

            # If we have collected 50 releases, write out our completed releases page
            if build_tree_dict["releases_release_counter"] == query_rows:
                # Record that we built a page
                total_pages_num += 1
                build_tree_dict["releases_pages"] += 1
                releases_page_metadata_path = director_path + "/releases/pages/" + str(build_tree_dict["releases_pages"]) + ".json"
                with open(releases_page_metadata_path, 'w') as releases_page_metadata_file:
                    json.dump(releases_page_release_list, releases_page_metadata_file)
                releases_page_metadata_file.close()
                # Reset the counter
                build_tree_dict["releases_release_counter"] = 1
                # Empty the release list
                releases_page_release_list = []

            # If we have collected 50 featured releases (or 50 in a category), do the same
            if build_tree_dict["featured_release_counter"] == query_rows:
                # Record that we built a page
                total_pages_num += 1
                build_tree_dict["featured_pages"] += 1
                featured_page_metadata_path = director_path + "/featured/pages/" + str(build_tree_dict["featured_pages"]) + ".json"
                with open(featured_page_metadata_path, 'w') as featured_page_metadata_file:
                    json.dump(featured_page_release_list, featured_page_metadata_file)
                featured_page_metadata_file.close()
                # Reset the counter
                build_tree_dict["featured_release_counter"] = 0
                # Empty the release list
                featured_page_release_list = []

            for featured_category in build_tree_dict["featured_categories"]:
                if build_tree_dict["featured_category_data"][featured_category]["category_release_counter"] > query_rows:
                    # Record that we built a page
                    total_pages_num += 1
                    build_tree_dict["featured_category_data"][str(featured_category)]["category_pages"] += 1
                    category_page_metadata_path = director_path + "/featured/category/pages/" + str(build_tree_dict["featured_category_data"][str(featured_category)]["category_pages"]) + ".json"
                    with open(category_page_metadata_path, 'w') as category_page_metadata_file:
                        json.dump(build_tree_dict["featured_category_data"][str(featured_category)]["category_release_list"], category_page_metadata_file)
                    category_page_metadata_file.close()
                    # Reset the counter
                    build_tree_dict["featured_release_counter"] = 0
                    # Empty the release list
                    build_tree_dict["featured_category_data"][str(featured_category)]["category_release_list"] = []

        if cursor.rowcount < query_rows:
            print("Reached the end, checking there are no more rows to fetch...")
            fetch_data()
            if cursor.rowcount == 0:
                print("Successfully fetched all data from the database.")
                # Record that we have successfully finished retrieving data
                end_of_set = 1

                # Collect leftovers for each type:
                # All releases
                if build_tree_dict["releases_release_counter"] > 0:
                    # Record that we built a page
                    total_pages_num += 1
                    build_tree_dict["releases_pages"] += 1
                    releases_page_metadata_path = director_path + "/releases/pages/" + str(
                        build_tree_dict["releases_pages"]) + ".json"
                    with open(releases_page_metadata_path, 'w') as releases_page_metadata_file:
                        json.dump(releases_page_release_list, releases_page_metadata_file)
                    releases_page_metadata_file.close()
                    # Reset the counter
                    build_tree_dict["releases_release_counter"] = 0
                    # Empty the release list
                    releases_page_release_list = []

                # Featured releases
                if build_tree_dict["featured_release_counter"] > 0:
                    # Record that we built a page
                    total_pages_num += 1
                    build_tree_dict["featured_pages"] += 1
                    featured_page_metadata_path = director_path + "/featured/pages/" + str(
                        build_tree_dict["featured_pages"]) + ".json"
                    with open(featured_page_metadata_path, 'w') as featured_page_metadata_file:
                        json.dump(featured_page_release_list, featured_page_metadata_file)
                    featured_page_metadata_file.close()
                    # Reset the counter
                    build_tree_dict["featured_release_counter"] = 0
                    # Empty the release list
                    featured_page_release_list = []

                for featured_category in build_tree_dict["featured_categories"]:
                    if build_tree_dict["featured_category_data"][featured_category]["category_release_counter"] > 0:
                        # Record that we built a page
                        total_pages_num += 1
                        build_tree_dict["featured_category_data"][str(featured_category)]["category_pages"] += 1
                        category_page_metadata_path = director_path + "/featured/category/" + featured_category + "/pages/" + str(build_tree_dict["featured_category_data"][str(featured_category)]["category_pages"]) + ".json"
                        with open(category_page_metadata_path, 'w') as category_page_metadata_file:
                            json.dump(build_tree_dict["featured_category_data"][str(featured_category)]["category_release_list"], category_page_metadata_file)
                        category_page_metadata_file.close()
                        # Reset the counter
                        build_tree_dict["featured_release_counter"] = 0
                        # Empty the release list
                        build_tree_dict["featured_category_data"][str(featured_category)]["category_release_list"] = []

            else:
                die_message = "Something weird is going on, check The Curator."
                print(die_message)
                sys.exit(die_message)

    build_all_pages_timer_done = time.perf_counter()
    print(f"Built {total_pages_num} pages in {build_all_pages_timer_done - build_all_pages_timer:0.4f} seconds in folder {director_path}")

def add_to_ipfs(target_path):
    add_to_ipfs_timer = time.perf_counter()
    try:
        ipfs_added_path = ipfs_connection.add(target_path)
        add_to_ipfs_timer_done = time.perf_counter()
        print(f"Published {target_path} to IPFS in {add_to_ipfs_timer_done - add_to_ipfs_timer:0.4f} seconds")
        return ipfs_added_path[-1]['Hash']
    except Exception as e:
        print("Tried to add " + target_path + " to IPFS but there was an issue.")
        print(e)
        sys.exit("COULD_NOT_ADD_TO_IPFS")

def add_to_ipfs_single(target_path):
    add_to_ipfs_timer = time.perf_counter()
    try:
        ipfs_added_path = ipfs_connection.add(target_path)
        add_to_ipfs_timer_done = time.perf_counter()
        print(f"Published {target_path} to IPFS in {add_to_ipfs_timer_done - add_to_ipfs_timer:0.4f} seconds")
        return ipfs_added_path['Hash']
    except Exception as e:
        print("Tried to add " + target_path + " to IPFS but there was an issue.")
        print(e)
        sys.exit("COULD_NOT_ADD_TO_IPFS")


def build_main_metadata():
    global releases_folder_ipfs_hash
    global build_tree_dict
    metadata_main_dict = {}
    releases_main_dict = {}
    featured_main_dict = {}
    available_apis = ["1.0.0"]

    metadata_main_dict["available_apis"] = available_apis
    metadata_main_dict["api_version"] = api_version
    releases_main_dict["pages"] = build_tree_dict["releases_pages"]
    releases_main_dict["pages_folder"] = releases_folder_ipfs_hash
    releases_main_dict["release_id_folder"] = release_id_folder_ipfs_hash
    featured_main_dict["pages"] = build_tree_dict["featured_pages"]
    featured_main_dict["pages_folder"] = featured_folder_ipfs_hash
    metadata_main_dict["releases"] = releases_main_dict
    metadata_main_dict["featured"] = featured_main_dict

    # Write out our completed page
    main_metadata_file = director_path + "/main.json"
    with open(main_metadata_file, 'w') as main_metadata_file:
        json.dump(metadata_main_dict, main_metadata_file)
    main_metadata_file.close()

    # Return the completed metadata file for debugging
    return(json.dumps(metadata_main_dict))


# Connect to our local IPFS daemon
ipfs_connection = ipfshttpclient.connect()
# Create a timer so we can track how long tasks take
global_timer = time.perf_counter()
# Declare some empty and starting variables/objects.
total_number_of_releases = 0
cursor = ""
director_path = ""
build_tree_dict = {}
# Statically set some variables
api_version = "1.0.0"  # We'll begin proper versioning once there's an app consuming the API

print("Welcome to Riff.CC. Let's free the world's culture, together.")
print("The Director will create a metadata tree and publish it to IPFS.")
if(force_new_publication):
    print("Special mode activated - will force IPFS to rehash everything as we build this.")
director_timestamp = setup_timestamp()
create_director_folder()
create_subfolder("releases/pages")
create_subfolder("releases/release_id")
create_subfolder("featured/pages")
setup_cursor("DECLARE director_cur CURSOR FOR SELECT * FROM releases ORDER BY id;")
build_all_pages()
destroy_cursor()

print("Adding the releases folder to IPFS.")
releases_folder_ipfs_hash = add_to_ipfs(director_path + "/releases/pages")
print("Adding the release_id folder to IPFS.")
release_id_folder_ipfs_hash = add_to_ipfs(director_path + "/releases/release_id")
print("Adding the featured releases folder to IPFS.")
featured_folder_ipfs_hash = add_to_ipfs(director_path + "/featured/pages")
# TODO: Add the tree for our featured release categories
m = build_main_metadata()
print("Look what I made... \n" + m)
complete_metadata_ipfs_hash = add_to_ipfs_single(director_path + "/main.json")
# publish_to_bch_testnet()

# Calculate the total run time
global_timer_done = time.perf_counter()
print("Published the entire platform as " + complete_metadata_ipfs_hash)
print("Total of " + str(total_number_of_releases) + " releases published.")
print(f"The Director is finished. Transpilation and publication took {global_timer_done - global_timer:0.4f} seconds.")

# TODOs: (things the script does not do yet)
# warn if something was deleted (possibly should be handled by curator) and made it into our dataset anyway
# shell out to Sentinel and Janitor to validate data
# build the featured files
# build the featured categories
# build the deleted IDs (and hashes during testing)
# pull relationships from the Curator
# build the related relationships for releases
# build the related relationships for artists
# do a single loop and separate how many items per page from how many items per query
#
# Developer notes:
# While we could cast category_ids etc to actual categories within The Director,
# it makes more sense to have them defined in the database and built as a separate bit of metadata_ids in the metadata.
# This allows for dynamism, and we can also fairly trivially cast them to "actual types" later, or even do both at once.
# During debugging we may simply do both at once, then drop the "actual types" to keep metadata lighter.
