from biometric.Bio import Bio
import os.path

workdir = os.path.dirname(os.path.realpath(__file__)) + "/"

try:
    b = Bio(workdir)
    print(b.requestFPrint())
except:
    print("ERROR")
