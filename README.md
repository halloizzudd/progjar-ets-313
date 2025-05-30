#Pemrograman Jaringan - ETS

---

## 📦 Menjalankan Server

```bash
python file_server.py --host [IP_ADDRESS] --port [PORT] --method [thread|process] --workers [JUMLAH_WORKERS]
```

---


## 📦 

Membuat file dummy
``` fallocate -l 10M file_10MB.dat
fallocate -l 50M file_50MB.dat
fallocate -l 100M file_100MB.dat
```
Menjalankan server multiproses
```
python3 file_server.py --operation server --pool {jumlah pool}
```
Menjalankan sever Multithread
```
python3 file_server.py --operation thread --pool {jumlah pool}
```
Menjalankan Client
```
python file_client_cli.py stress --task <upload|download|list> --size <10|50|100> --workers <1|5|50> [--method thread|process]
```
atau
```
python file_client_cli.py cli cli --command <list|get|upload|delete> [--file nama_file]
```
