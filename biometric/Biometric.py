## get fingerprint hash
###### 3-fingers , each finger, 3 times ---> take most common hash
###### derive keys , using ECC class

##capture picture and convert to BLOB
import time
from pyfingerprint.pyfingerprint import PyFingerprint
import hashlib


class Biometric:
    def __init__(self):
        self.initialize()
        return

    def initialize(self):
        self.f = PyFingerprint('/dev/ttyUSB0', 57600, 0xFFFFFFFF, 0x00000000)
        if not self.f.verifyPassword():
            raise ValueError('The given fingerprint sensor password is wrong!')

    def getSureHash(self):
        hash1 = self.getFPrintHash()
        hash2 = self.getFPrintHash()
        hash3 = self.getFPrintHash()
        hash4 = self.getFPrintHash()
        return self.most_frequent()


    def most_frequent(self,List):
        counter = 0
        num = List[0]

        for i in List:
            curr_frequency = List.count(i)
            if (curr_frequency > counter):
                counter = curr_frequency
                num = i

        return num

    def getFPrintHash(self):
        # Wait that finger is read
        while not self.f.readImage():
            pass

        # Converts read image to characteristics and stores it in charbuffer 1
        self.f.convertImage(0x01)

        # Checks if finger is already enrolled
        result = self.f.searchTemplate()
        positionNumber = result[0]

        if positionNumber >= 0:
            return self.getHash(positionNumber)

        time.sleep(2)

        # Wait that finger is read again
        while not self.f.readImage():
            pass

        # Converts read image to characteristics and stores it in charbuffer 2
        self.f.convertImage(0x02)
        # Compares the charbuffers
        if self.f.compareCharacteristics() == 0:
            raise Exception('Fingers do not match')
        # Creates a template
        self.f.createTemplate()
        # Saves template at new position number
        positionNumber = self.f.storeTemplate()
        return self.getHash(positionNumber)

    def getHash(self, positionNumber):
        # Loads the found template to charbuffer 1
        self.f.loadTemplate(positionNumber, 0x01)
        # Downloads the characteristics of template loaded in charbuffer 1
        characterics = str(self.f.downloadCharacteristics(0x01)).encode('utf-8')
        # Hashes characteristics of template
        fprint_hash = hashlib.sha256(characterics).hexdigest()
        return fprint_hash
