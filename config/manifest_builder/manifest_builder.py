#!/usr/bin/env python3

"""ESF Add-ons manifest builder script

This script builds the manifest.json file needed by the artifact repository
for the ESF Add-ons artifacts.
It will compute the md5 and size of every file in the folder passed as argument
and correctly populate the manifest.json file in the same directory.
This script is intended to be used inside the RC build Jenkins pipeline of
the ESF add-ons.
"""

import argparse
import csv
import glob
import hashlib
import json
import os
import re


def parseDescriptionCSVFile(file_path):
    """Parses the CSV file passed as argument and builds a dictionary containing its informations"""

    dict = {}

    with open(file_path) as file:
        reader = csv.reader(file)

        for row in reader:
            artifactID, description, version = row
            dict[artifactID] = { "description": description, "version": version}

    return dict


def retrieveCategory(filename):
    """Retrieves category information for the filename passed as argument"""

    if ".txt" in filename:
        return "Release Notes"

    return "Add-ons"


def retrieveDescription(filename, csv_descriptions):
    """Retrieves the description for the filename passed as argument using the CSV file content"""

    if ".txt" in filename:
        return "Release notes"

    # Filename and version are separated by a "-" for .jar files, by "_" for .dp
    version_seperator = "-" if ".jar" in filename else "_"

    # Retrieve filename without the full path
    base_filename = os.path.basename(filename)
    # Retrieve filename without the extension
    noext_filename = os.path.splitext(base_filename)[0]

    for artifactID, values in csv_descriptions.items():
        # Build the expected name from the artifactID and the version stored in the CSV file
        expected_name = "%s%s%s" % (artifactID, version_seperator, values.get("version"))

        if noext_filename == expected_name:
            return values.get("description")

    print("No match found for '%s'. Setting placeholder description." % base_filename)
    return "placeholder"


def main():
    # Get CLI arguments
    parser = argparse.ArgumentParser(description="ESF Add-ons manifest builder script", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("-f", "--folder_path", type=str, help="Folder path where the files are stored and where the computed manifest file will be saved", required=True)
    parser.add_argument("-v", "--project_version", type=str, help="Project version as reported by maven", required=True)
    parser.add_argument("-n", "--project_name", type=str, help="Project name as reported by maven", required=True)
    parser.add_argument("-b", "--build_number", type=int, help="Build number as reported by the Jenkins build", required=True)
    parser.add_argument("-c", "--csv_file_path", type=str, required=True,
                        help="File path to the .csv file containing artifact descriptions.\n"
                            "The file can be generated with the following command:\n"
                            "mvn --file ./pom.xml \n"
                            "    -Dexec.executable=echo\n"
                            "    -Dexec.args='${project.artifactId},${project.name},${project.version}'\n"
                            "    --quiet exec:exec > file.csv")

    args = parser.parse_args()

    # Find all files in desired directory
    path = os.path.abspath(args.folder_path)
    filenames = glob.glob(os.path.join(path, "*"))

    # Parse CSV file
    csv_descriptions = parseDescriptionCSVFile(args.csv_file_path)

    # Files descriptor array
    files_array = []

    for filename in filenames:
        # Compute md5 hash
        md5hash = ''
        with open(filename, 'rb') as inputfile:
            data = inputfile.read()
            md5hash = hashlib.md5(data).hexdigest()

        # Compute size
        size = os.path.getsize(filename)

        # Decide visibility
        visibility = (".dp" in filename or ".txt" in filename)

        # Decide category and description field
        category = retrieveCategory(filename)
        description = retrieveDescription(filename, csv_descriptions)

        # Append dictionary to files descriptor array
        files_array.append({
            "category": category,
            "description": ("%s (%s)" % (description, args.project_version)),
            "name": os.path.basename(filename),
            "visible": visibility,
            "md5": md5hash,
            "size": size
        })

    # Build json object
    data = {
        "files": files_array,
        "product": args.project_name,
        "version": ("%s_%d" % (args.project_version, args.build_number)),
        "public": False
    }

    # Write json content on file
    manifest_path = os.path.join(path, 'manifest.json')
    with open(manifest_path, 'w', encoding='utf-8') as manifest_file:
        json.dump(data, manifest_file, indent=4, ensure_ascii=False)


if __name__ == '__main__':
    main()
