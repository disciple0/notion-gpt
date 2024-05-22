import argparse
import json
import os

from blueprints.architect import process_blueprint


'''LOAD ENVIRONMENT VARIABLES'''
from dotenv import load_dotenv
load_dotenv()
NOTION_PAGE_ID = os.getenv('NOTION_PAGE_ID')


def load_blueprint(filename):
    with open(filename, "r") as file:
        return json.load(file)


def main():
    parser = argparse.ArgumentParser(description="Process a JSON blueprint to create content in Notion.")
    parser.add_argument("json_file", help="Location of the JSON blueprint file")
    args = parser.parse_args()

    blueprint = load_blueprint(args.json_file)
    process_blueprint(NOTION_PAGE_ID, blueprint)


if __name__ == "__main__":
    main()
