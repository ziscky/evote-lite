from biometric.Biometric import Biometric
import os.path

workdir = os.path.dirname(os.path.realpath(__file__)) + "/"

try:
    b = Biometric()
    print(b.getFPrintHash())
except Exception as e:
    print("ERROR:", e)
