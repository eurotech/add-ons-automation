#!/usr/bin/env python3

"""ESF Add-ons manifest builder script

This script builds the manifest.json file needed by the artifact repository
for the ESF Add-ons artifacts.
It will compute the md5 and size of every file in the folder passed as argument
and correctly populate the manifest.json file in the same directory.
This script is intended to be used inside the RC build Jenkins pipeline of
the ESF add-ons.
"""

import os
import glob
import hashlib
import json
import argparse


def retrieveCategory(filename):
    if ".txt" in filename:
        return "Release Notes"

    return "Add-ons"


def retrieveDescription(filename):
    # TODO
    if ".txt" in filename:
        return "Release notes"

    return "placeholder"


def main():
    # Get CLI arguments
    parser = argparse.ArgumentParser(description="ESF Add-ons manifest builder script")
    parser.add_argument("-f", "--folder_path", help="Folder path where the files are stored and where the computed manifest file will be saved", required=True)
    parser.add_argument("-v", "--project_version", help="Project version as reported by maven", required=True)
    parser.add_argument("-n", "--project_name", help="Project name as reported by maven", required=True)
    parser.add_argument("-b", "--build_number", help="Build number as reported by the Jenkins build", required=True)

    args = parser.parse_args()

    # Find all files in desired directory
    path = os.path.abspath(args.folder_path)
    filenames = glob.glob(os.path.join(path, "*"))

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
        description = retrieveDescription(filename)

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
        "version": ("%s_%s" % (args.project_version, args.build_number)),
        "public": False
    }

    # Write json content on file
    manifest_path = os.path.join(path, 'manifest.json')
    with open(manifest_path, 'w', encoding='utf-8') as manifest_file:
        json.dump(data, manifest_file, indent=4, ensure_ascii=False)


if __name__ == '__main__':
    main()
