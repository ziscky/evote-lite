import subprocess

class Bio:
    def __init__(self,workdir):
        self.workdir = workdir
        return

    def requestFPrint(self):
        hash = subprocess.check_output(["python2",self.workdir+"/fprint.py"]).decode("utf-8")
        return hash.strip('\n')
