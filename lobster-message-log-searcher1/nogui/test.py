import os


file = "13_05_2025_message.log"

filename = os.path.basename(file)[:10]
new_filename= filename.replace("_", " ")

print(new_filename)
