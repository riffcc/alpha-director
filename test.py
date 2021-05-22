from datetime import datetime

director_timestamp = datetime.now()

print(director_timestamp)

current_time = director_timestamp.strftime("%%H:%M:%S")