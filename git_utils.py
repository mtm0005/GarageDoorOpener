import os
import subprocess

import utils

def git_pull():
    # Move to the project path.
    project_path = os.path.realpath(os.path.dirname(__file__))
    os.chdir(project_path)

    try:
        raw_output = subprocess.check_output('git pull'.split())
    except BaseException as e:
        utils.log_info('git pull exception', data=e)
        return ''

    return raw_output.decode('ascii')

def git_tag():
    # Move to the project path.
    project_path = os.path.realpath(os.path.dirname(__file__))
    os.chdir(project_path)

    try:
        raw_output = subprocess.check_output('git tag --sort=-refname'.split())
    except BaseException as e:
        return e

    output = raw_output.decode('ascii')

    return output.split()[0]
