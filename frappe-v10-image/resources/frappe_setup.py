# imports - standard imports
import os, shutil
from distutils.command.clean import clean as Clean

from setuptools import setup, find_packages
# from pip.req import parse_requirements # Original line, now commented out

import re, ast

# --- START PATCHED SECTION ---
# Custom function to parse requirements.txt without relying on pip.req
# This avoids the "ImportError: No module named req" and "NameError: name 'parse_requirements' is not defined"
def get_requirements(file):
    requirements = []
    with open(file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                requirements.append(line)
    return requirements
# --- END PATCHED SECTION ---

# get version from __version__ variable in frappe/__init__.py
_version_re = re.compile(r'__version__\s+=\s+(.*)')

with open('frappe/__init__.py', 'rb') as f:
    version = str(ast.literal_eval(_version_re.search(
        f.read().decode('utf-8')).group(1)))

# requirements = parse_requirements("requirements.txt", session="") # Original line
requirements = get_requirements("requirements.txt") # Patched: use custom function

class CleanCommand(Clean):
    def run(self):
        Clean.run(self)

        basedir = os.path.abspath(os.path.dirname(__file__))

        for relpath in ['build', '.cache', '.coverage', 'dist', 'frappe.egg-info']:
            abspath = os.path.join(basedir, relpath)
            if os.path.exists(abspath):
                if os.path.isfile(abspath):
                    os.remove(abspath)
                else:
                    shutil.rmtree(abspath)

        for dirpath, dirnames, filenames in os.walk(basedir):
            for filename in filenames:
                _, extension = os.path.splitext(filename)
                if extension in ['.pyc']:
                    abspath = os.path.join(dirpath, filename)
                    os.remove(abspath)
            for dirname in dirnames:
                if dirname in ['__pycache__']:
                    abspath = os.path.join(dirpath,  dirname)
                    shutil.rmtree(abspath)

setup(
	name='frappe',
	version=version,
	description='Metadata driven, full-stack web framework',
	author='Frappe Technologies',
	author_email='info@frappe.io',
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	# install_requires needs to be a list of strings directly
	install_requires=requirements, # Now uses the list of strings from get_requirements
	# dependency_links will be empty with this simple parsing, removing the original line
	# dependency_links=[str(ir._link) for ir in requirements if ir._link],
	cmdclass = \
	{
		'clean': CleanCommand
	}
)
