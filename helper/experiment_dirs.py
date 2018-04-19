import datetime
import time
import os

SYMLINK_NAME = "latest"

def generate_new(root):
    if not os.path.exists(root):
        os.makedirs(root)

    path = try_now(root)

    if len(path) == 0:
        time.sleep(1)
        path = try_now(root)
        assert(len(path) > 0) # now the time should have advanced enough

    return path

def try_now(root):
    owd = os.getcwd()
    try:
        os.chdir(root)

        name = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
       
        if os.path.exists(name):
            return ""

        os.makedirs(name)

        # Relink symlink
        try:
            os.remove(SYMLINK_NAME)
        except OSError:
            pass # not existing so no problem
        os.symlink(name,SYMLINK_NAME)

        return os.path.join(root,name)
    finally:
        os.chdir(owd)

