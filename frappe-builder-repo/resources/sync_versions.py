#!/usr/bin/env python3
import argparse
import json
import os
import re
import sys
from importlib.machinery import SourceFileLoader

SKIP_APPS = [
    "frappe",
    "castlecraft",
    "frappe_utils",
]


def get_args_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("apps_json", help="path to apps.json")
    parser.add_argument(
        "--apps-path",
        help="path to frappe-bench/apps",
        default="/home/frappe/frappe-bench/apps",
    )
    return parser


def parse_json_file(path):
    file_contents = None
    with open(path) as user_file:
        file_contents = user_file.read()
    return json.loads(file_contents)


def get_app_name_and_tag(apps):
    out = []
    for app in apps:
        out.append(
            {
                "name": app.get("url").split("/")[-1].replace(".git", ""),
                "tag": app.get("branch"),
            }
        )
    return out


def get_bench_apps(apps_path):
    bench_apps = None
    try:
        bench_apps = next(os.walk(apps_path))[1]
    except StopIteration:
        print("Invalid bench path")
        sys.exit(1)
    return bench_apps


def main():
    parser = get_args_parser()
    args = parser.parse_args()
    apps = parse_json_file(args.apps_json)
    apps = get_app_name_and_tag(apps)
    bench_apps = get_bench_apps(args.apps_path)
    for app in apps:
        app_name = app.get("name")
        app_tag = app.get("tag")
        if app_name in bench_apps and app_name not in SKIP_APPS:
            init_file_path = (
                f"{args.apps_path}/{app_name}/{app_name}/__init__.py"  # noqa: E501
            )
            init_version = SourceFileLoader(
                "init_version", init_file_path
            ).load_module()
            if app_tag != init_version.__version__:
                print(f"patching __version__ for {app_name} to {app_tag}")
                with open(init_file_path, "r+") as f:  # noqa: E501
                    content = f.read()
                    content = re.sub(
                        r"__version__ = .*",
                        f'__version__ = "{app_tag}"',
                        content,  # noqa: E501
                    )
                    f.seek(0)
                    f.truncate()
                    f.write(content)
            else:
                print(
                    f"Skip patching __version__ for {app_name} to app_tag: {app_tag} as it matches with init_version: {init_version.__version__}"  # noqa: E501
                )


if __name__ == "__main__":
    main()

# usage: sync_versions.py [-h] [--apps-path APPS_PATH] apps_json
# python sync_versions.py /path/to/apps.json
