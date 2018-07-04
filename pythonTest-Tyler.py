# Test python file
import os
import subprocess


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

result = git_tag()

print(result)