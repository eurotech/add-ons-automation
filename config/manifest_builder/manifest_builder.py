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
import logging


def compute_MD5_hash(file_path):
    """Computes the MD5 hash of the file passed as argument"""

    md5hash = ''
    with open(file_path, 'rb') as inputfile:
        data = inputfile.read()
        md5hash = hashlib.md5(data).hexdigest()

    return md5hash


def parse_description_CSV_file(file_path):
    """Parses the CSV file passed as argument and builds a dictionary containing its informations"""

    dict = {}

    with open(file_path) as file:
        reader = csv.reader(file)

        for row in reader:
            artifactID, description, version = row
            dict[artifactID] = { "description": description, "version": version}

    return dict


def retrieve_category(filename):
    """Retrieves category information for the filename passed as argument"""

    if ".txt" in filename:
        return "Release Notes"

    return "Add-ons"


def retrieve_description(filename, csv_descriptions):
    """ Retrieves the description for the filename passed as argument using the CSV file content

        To match the file to the Artifact ID (and then the description) we compare the CSV file content (artifact id + version) and the filename.
        Knowing the artifact id and the version we can reconstruct the resulting filename and thus match with the corresponding description.
    """

    if ".txt" in filename:
        return "Release notes"

    # Filename and version are separated by a "-" for .jar files, by "_" for .dp
    version_seperator = "-" if ".jar" in filename else "_"

    # Retrieve filename without the full path
    base_filename = os.path.basename(filename)
    # Retrieve filename without the extension
    noext_filename = os.path.splitext(base_filename)[0]

    for artifactID, values in csv_descriptions.items():
        #??Build the expected name from the artifactID and the version stored in the CSV file
        expected_name = "%s%s%s" % (artifactID, version_seperator, values.get("version"))

        if noext_filename == expected_name:
            if artifactID == values.get("description"):
                logging.warning("ArtifactID and description match for '%s'. Was the pom.xml updated with the correct name?" % artifactID)

            return ("%s (%s)" % (values.get("description"), values.get("version")))

    logging.warning("No match found for '%s'. Setting placeholder description." % base_filename)
    return "placeholder"


def main():
    # Get CLI arguments
    parser = argparse.ArgumentParser(description="ESF Add-ons manifest builder script", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("-d", "--debug", dest="loglevel", help="enable debug logging", required=False, default=logging.WARNING, const=logging.DEBUG, action="store_const")
    parser.add_argument("-f", "--folder_path", type=str, help="Folder path where the files are stored and where the computed manifest file will be saved", required=True)
    parser.add_argument("-v", "--project_version", type=str, help="Root project version as reported by maven", required=True)
    parser.add_argument("-n", "--project_name", type=str, help="Root project ArtifactID as reported by maven", required=True)
    parser.add_argument("-b", "--build_number", type=int, help="Build number as reported by the Jenkins build", required=True)
    parser.add_argument("-c", "--csv_file_path", type=str, required=True,
                        help="File path to the .csv file containing artifact descriptions.\n"
                            "The file can be generated with the following command:\n"
                            "mvn --file ./pom.xml \n"
                            "    -Dexec.executable=echo\n"
                            "    -Dexec.args='${project.artifactId},${project.name},${project.version}'\n"
                            "    --quiet exec:exec > file.csv")

    args = parser.parse_args()
    logging.basicConfig(level=args.loglevel)

    # Find all files in desired directory
    logging.info("Running manifest builder script in '%s'" % args.folder_path)

    path = os.path.abspath(args.folder_path)
    if not os.path.isdir(path):
        logging.error("Path '%s' is not a directory" % path)
        exit(1)

    filenames = glob.glob(os.path.join(path, "*"))
    if not filenames:
        logging.error("No files found in path: '%s'" % path)
        exit(1)

    # Parse CSV file
    logging.info("Parsing CSV file at: '%s'" % args.csv_file_path)
    csv_descriptions = parse_description_CSV_file(args.csv_file_path)

    # Files descriptor array
    files_array = []
    for filename in filenames:
        # Compute metadata
        category    = retrieve_category(filename)
        description = retrieve_description(filename, csv_descriptions)
        visibility  = (".dp" in filename or ".txt" in filename)
        md5hash     = compute_MD5_hash(filename)
        size        = os.path.getsize(filename)

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
        "product": args.project_name,
        "version": ("%s_%d" % (args.project_version, args.build_number)),
        "public": False
    }

    # Write json content on file
    manifest_path = os.path.join(path, 'manifest.json')
    logging.info("Writing resulting file in: '%s'" % manifest_path)
    with open(manifest_path, 'w', encoding='utf-8') as manifest_file:
        json.dump(data, manifest_file, indent=4, ensure_ascii=False)


if __name__ == '__main__':
    main()
