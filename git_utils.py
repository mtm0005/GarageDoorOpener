import os
import subprocess

import utils

@utils.try_thrice
def git_pull():
    # Move to the project path.
    project_path = os.path.realpath(os.path.dirname(__file__))
    os.chdir(project_path)

    raw_output = subprocess.check_output('git pull'.split())

    return raw_output.decode('ascii')

@utils.try_thrice
def git_tag():
    # Move to the project path.
    project_path = os.path.realpath(os.path.dirname(__file__))
    os.chdir(project_path)

    raw_output = subprocess.check_output('git tag --sort=-refname'.split())

    output = raw_output.decode('ascii')

    return output.split()[0]
