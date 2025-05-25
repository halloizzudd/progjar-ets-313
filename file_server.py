import socket
import logging
import time
import concurrent.futures
from multiprocessing import Pool, cpu_count, current_process

from file_protocol import FileProtocol

# Aktifkan logging
logging.basicConfig(level=logging.INFO)

# Fungsi global yang akan dipanggil oleh process pool
def proses_data(data):
    fp = FileProtocol()
    hasil = fp.proses_string(data)
    return hasil + "\r\n\r\n"

# Fungsi untuk menangani client (dieksekusi dalam thread pool)
def handle_client(connection, address):
    try:
        while True:
            length_data = b''
            while len(length_data) < 10:
                more = connection.recv(10 - len(length_data))
                if not more:
                    raise Exception("Connection closed while reading length header")
                length_data += more
            total_length = int(length_data.decode())

            try:
                total_length = int(length_data.decode())
                if total_length > 10**9:
                    raise ValueError("Data terlalu besar")
            except ValueError:
                logging.error(f"[{address}] Panjang data tidak valid")
                return

            data = b""
            while len(data) < total_length:
                more = connection.recv(min(512*1024, total_length - len(data)))
                if not more:
                    logging.warning(f"[{address}] Koneksi ditutup saat transfer")
                    return
                data += more

            d = data.decode()

            # Mulai hitung waktu proses
            start_time = time.perf_counter()
            try:
                hasil = proses_data(d)
                status = "BERHASIL"
            except Exception as e:
                hasil = f"[ERROR] Gagal memproses data: {str(e)}\n\n"
                status = "GAGAL"

            elapsed = time.perf_counter() - start_time
            logging.info(f"[{address}] Status Worker: {status}, Waktu proses: {elapsed:.3f}s")

            hasil_bytes = hasil.encode()
            length_prefix = str(len(hasil_bytes)).zfill(10).encode()
            try:
                connection.sendall(length_prefix + hasil_bytes)
                logging.info(f"[{address}] Balasan berhasil dikirim")
                break
            except (BrokenPipeError, ConnectionResetError) as e:
                logging.warning(f"[{address}] Gagal mengirim balasan: {e}")
                return

    except socket.timeout:
        logging.warning(f"[{address}] Timeout koneksi")
    except Exception as e:
        logging.error(f"[{address}] Error umum: {e}")
    finally:
        connection.close()
        logging.info(f"[{address}] Koneksi ditutup")

# Server class
class Server:
    def __init__(self, ipaddress='0.0.0.0', port=8889, max_workers=1, method='thread'):
        self.ipinfo = (ipaddress, port)
        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.max_workers = max_workers

        self.method = method.lower()
        self.executor_cls = concurrent.futures.ProcessPoolExecutor if method == 'process' else concurrent.futures.ThreadPoolExecutor

    def run(self):
        logging.warning(f"Server aktif di {self.ipinfo[0]}:{self.ipinfo[1]} "
                        f"(Mode: {self.method.upper()}, Workers: {self.max_workers})")
        self.my_socket.bind(self.ipinfo)
        self.my_socket.listen(self.max_workers)
        try:
            with self.executor_cls(max_workers=self.max_workers) as executor:
                while True:
                    connection, client_address = self.my_socket.accept()
                    logging.warning(f"[{client_address}] Terhubung")
                    executor.submit(handle_client, connection, client_address)
        except KeyboardInterrupt:
            logging.warning("Server dimatikan manual (Ctrl+C)")
        finally:
            self.shutdown()

    def shutdown(self):
        logging.warning("Menutup server...")
        self.executor_cls.shutdown(wait=True)
        self.my_socket.close()
        logging.warning("Server dimatikan.")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Flexible File Server")
    parser.add_argument("--host", default="0.0.0.0", help="Alamat IP server")
    parser.add_argument("--port", type=int, default=6667, help="Port server")
    parser.add_argument("--method", choices=['thread', 'process'], default='thread', help="Metode eksekusi: 'thread' atau 'process'")
    parser.add_argument("--workers", type=int, default=10, help="Jumlah worker thread")

    args = parser.parse_args()

    server = Server(
        ipaddress=args.host,
        port=args.port,
        max_workers=args.workers,
        method=args.method
    )
    server.run()
    
if __name__ == "__main__":
    main()