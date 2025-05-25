import json
import logging
import shlex

from file_interface import FileInterface

"""
* class FileProtocol bertugas untuk memproses
data yang masuk, dan menerjemahkannya apakah sesuai dengan
protokol/aturan yang dibuat

* data yang masuk dari client adalah dalam bentuk bytes yang
pada akhirnya akan diproses dalam bentuk string

* class FileProtocol akan memproses data yang masuk dalam bentuk
string
"""



class FileProtocol:
    def __init__(self):
        self.file = FileInterface()

    def proses_string(self, string_datamasuk=''):
        logging.warning(f"string sedang diproses")

        try:
            # Cek keyword perintah terlebih dahulu
            if string_datamasuk.startswith("UPLOAD "):
                parts = string_datamasuk.strip().split(" ", 2)
                if len(parts) != 3:
                    raise ValueError("Format UPLOAD tidak valid")
                command = parts[0].lower()
                filename = parts[1].strip()
                data = parts[2]
                params = [filename, data]
            elif string_datamasuk.startswith("LIST"):
                command = string_datamasuk.strip().lower()
                params = []
            else:
                parts = string_datamasuk.strip().split(" ", 1)
                if len(parts) != 2:
                    raise ValueError("Format GET tidak valid")
                command = parts[0].lower()
                filename = parts[1].strip()
                params = [filename]

            logging.warning(f"memproses request: {command}")

            if not hasattr(self.file, command):
                raise ValueError(f"Perintah '{command}' tidak dikenali")

            method = getattr(self.file, command)
            cl = method(params)
            return json.dumps(cl)

        except Exception as e:
            return json.dumps(dict(status='ERROR', data=f'request tidak dikenali atau error: {str(e)}'))


if __name__=='__main__':
    #contoh pemakaian
    fp = FileProtocol()
    print(fp.proses_string("LIST"))
    print(fp.proses_string("GET pokijan.jpg"))