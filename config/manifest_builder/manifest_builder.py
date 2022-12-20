#!/usr/bin/env python3

"""Artifact repository mainfest.json file builder script

This script builds the manifest.json file needed by the artifact repository.
It will compute the md5 and size of every file in the folder passed as argument
and correctly populate the manifest.json file in the same directory.
It also has an interactive mode for setting the description for every file in the
directory at run-time.
"""

import os
import glob
import hashlib
import json
import argparse


def main():
    # Get options
    parser = argparse.ArgumentParser(description="Artifact repository manifest.json file builder script")
    parser.add_argument("-f", "--folder_path", help="Folder path for the desired manifest file", required=True)
    parser.add_argument("-i", "--interactive_mode", help="Enable interactive mode", action="store_true", default=False)

    args = parser.parse_args()

    # Find all files in desired directory
    path = os.path.abspath(args.folder_path)
    filenames = glob.glob(os.path.join(path, "*"))

    # If in interactive mode ask user for version
    version = ""
    if args.interactive_mode:
        print("Version of the package: ")
        version = str(input(">:")).strip()
        print()

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
        category = "Add-ons"
        description = "placeholder"
        if ".txt" in filename:
            category = "Release Notes"
            description = "Release notes"

        # Ask description to user if interactive mode enabled
        if args.interactive_mode and description == "placeholder":
            print("Input description for '%s' omitting version ('s' for skipping file)" % os.path.basename(filename))
            description = str(input(">:")).strip()

            if description.lower() == "s":
                print()
                continue

            description = "%s (%s)" % (description, version)
            print()

        # Append dictionary to files descriptor array
        files_array.append({
            "category": category,
            "description": description,
            "name": os.path.basename(filename),
            "visible": visibility,
            "md5": md5hash,
            "size": size
        })

    # Build json object
    data = {
        "files": files_array,
        "product": "placeholder",
        "version": "placeholder",
        "public": False
    }

    # Write json content on file
    manifest_path = os.path.join(path, 'manifest.json')
    with open(manifest_path, 'w', encoding='utf-8') as manifest_file:
        json.dump(data, manifest_file, indent=4, ensure_ascii=False)

    print("Mainfest written to: ", manifest_path)

if __name__ == '__main__':
    main()
