import os
import json
import base64
from glob import glob

class FileInterface:
    def _sanitize(self, filename):
        if '..' in filename or '/' in filename or '\\' in filename:
            raise ValueError("Nama file tidak valid")
        return filename

    def list(self, params=[]):
        try:
            filelist = glob('files/*.*')
            return dict(status='OK', data=filelist)
        except Exception as e:
            return dict(status='ERROR', data=str(e))

    def get(self, params=[]):
        try:
            if len(params) < 1:
                raise ValueError("Parameter nama file kurang")
            safe_name = self._sanitize(params[0])
            filename = os.path.join(os.getcwd(), safe_name)
            if not os.path.exists(filename):
                raise FileNotFoundError("File tidak ditemukan")

            with open(filename, 'rb') as fp:
                isifile = base64.b64encode(fp.read()).decode()
            return dict(status='OK', data_namafile=filename, data_file=isifile)
        except Exception as e:
            return dict(status='ERROR', data=str(e))

    def upload(self, params=[]):
        try:
            if len(params) < 2:
                raise ValueError("Parameter tidak lengkap")

            filename = self._sanitize(params[0])
            encoded = params[1]

            with open(filename, 'wb') as fp:
                fp.write(base64.b64decode(encoded))
            return dict(status='OK', data=f"{filename} berhasil diupload")
        except Exception as e:
            return dict(status='ERROR', data=str(e))

    def delete(self, params=[]):
        try:
            if len(params) < 1:
                raise ValueError("Parameter nama file kurang")
            filename = self._sanitize(params[0])
            if not os.path.exists(filename):
                raise FileNotFoundError("File tidak ditemukan")

            os.remove(filename)
            return dict(status='OK', data=f"{filename} berhasil dihapus")
        except Exception as e:
            return dict(status='ERROR', data=str(e))

if __name__=='__main__':
    f = FileInterface()
    print(f.list())
    print(f.get(['pokijan.jpg']))