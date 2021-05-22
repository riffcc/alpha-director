from datetime import datetime

# Grab the current time UTC, then use it to create a fixed timestamp for this Director run/metadata set.
current_time = datetime.now()
director_timestamp = current_time.strftime("%Y%m%dT%H%M%SZ")

print(director_timestamp)
