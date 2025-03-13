#!/usr/bin/env python3

import argparse
import os
import sys
from jinja2 import Environment, FileSystemLoader, select_autoescape


def get_args_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-t",
        "--template",
        action="store",
        help="name of template from benches directory or directory specified in $APP_JSONS environment variable, e.g. production.json, staging.json",
    )
    return parser


def render_apps_json(args: argparse.Namespace):
    env = Environment(
        loader=FileSystemLoader(os.environ.get("APP_JSONS", "benches")),
        autoescape=select_autoescape(),
    )
    template = env.get_template(args.template)
    print(template.render(env=os.environ))  # noqa: T001, T002, T201, T202


def main():
    parser = get_args_parser()
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    args = parser.parse_args()
    render_apps_json(args)


if __name__ == "__main__":
    main()
