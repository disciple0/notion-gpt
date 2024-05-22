import argparse
import os
from functools import partial

from blueprints.architect import process_blueprint, generate_blueprint


'''LOAD ENVIRONMENT VARIABLES'''
from dotenv import load_dotenv
load_dotenv()
NOTION_PAGE_ID = os.getenv('NOTION_PAGE_ID')


def main():
    parser = argparse.ArgumentParser(description="Generates Notion content given a brief description")
    parser.add_argument("description", help="Text description of the desired content in Notion.")
    args = parser.parse_args()

    content = None
    for update in generate_blueprint(args.description):
        if isinstance(update, dict):
            content = update
        else:
            print(update, end="", flush=True)

    blueprint = content["blueprint"]
    process_blueprint(NOTION_PAGE_ID, blueprint)


if __name__ == "__main__":
    main()
