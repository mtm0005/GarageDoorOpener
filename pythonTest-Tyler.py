# Test python file
import os
import subprocess


def git_pull():
    # Move to the project path.
    project_path = os.path.realpath(os.path.dirname(__file__))
    os.chdir(project_path)

    try:
        #raw_output = subprocess.check_output('git pull'.split())
        raw_output = subprocess.check_output('git branch'.split())
    except BaseException as e:
        return e

    return raw_output.decode('ascii')

result = git_pull()

print(result)

if result == '* master\n':
    print('yepp')