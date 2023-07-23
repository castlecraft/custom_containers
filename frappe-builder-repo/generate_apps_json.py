import argparse
import os
from jinja2 import Environment, FileSystemLoader, select_autoescape


def get_args_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-t",
        "--template",
        action="store",
        help="path to template",
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
    args = parser.parse_args()
    render_apps_json(args)


if __name__ == "__main__":
    main()
