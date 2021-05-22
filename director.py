#!/usr/bin/python3
# "a piece of knowledge, unlike a piece of physical property, can be shared by large groups of people without making anybody poorer."
# - Aaron Swartz
# In loving memory. This is for you.

# Import needed modules
from __future__ import with_statement
import os
import yaml
import psycopg2
import sys

# Define methods
def fetch_release_rows():
    print("Building page " + str(pageNum) + " as a group of " + str(page_rows) + " releases.")
    sql = "FETCH " + str(page_rows) + " FROM director_cur;"
    cursorpg.execute(sql)
    result_set = cursorpg.fetchall()

def build_page():
    for row in result_set:
        # For every existing release, gather relevant metadata and massage it into Curator.
        release_id = row[0]
        print("DEBUG id: " + str(release_id))

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

# import data from postgres

# initial setup

# verification (optional)
# shell out to Sentinel and Janitor to validate data

# build the releases pages
# build the main releases files
# build the featured files
# build the featured categories
# build the deleted IDs and hashes

# pull from the Curator
# build the related relationships for releases
# build the related relationships for artists

# create a cursor
cursorpg = connpg.cursor()

# Open a read cursor
# https://www.citusdata.com/blog/2016/03/30/five-ways-to-paginate/
sql = "DECLARE director_cur CURSOR FOR SELECT * FROM releases ORDER BY id;"
cursorpg.execute(sql)