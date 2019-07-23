import subprocess

class Bio:
    def __init__(self,workdir):
        self.workdir = workdir
        return

    def requestFPrint(self):
        subprocess.check_output(["python2",self.workdir+"/fprint.py"])
        pass