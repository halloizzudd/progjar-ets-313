# ets-progjar

---

## 📦 Menjalankan Server

```bash
python file_server.py --host [IP_ADDRESS] --port [PORT] --method [thread|process] --workers [JUMLAH_WORKERS]
```

---


## 📦 Menjalankan Client
```bash
python file_client_cli.py stress --task <upload|download|list> --size <10|50|100> --workers <1|5|50> [--method thread|process]
```
atau
```bash
python file_client_cli.py cli cli --command <list|get|upload|delete> [--file nama_file]
```

## 👨‍💻 Author
ETS Pemrograman Jaringan - Choirul Anam