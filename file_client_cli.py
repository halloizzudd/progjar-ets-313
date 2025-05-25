import socket
import json
import base64
import logging
import sys
import os
import time
import concurrent.futures
import argparse

# Konfigurasi logging
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')

server_address = ('172.16.16.101', 6667)

def send_command(command_str=""):
    global server_address
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(server_address)
    logging.warning(f"connecting to {server_address}")
    try:
        logging.warning("sending message")
        encoded_command = command_str.encode()
        length_str = str(len(encoded_command)).zfill(10).encode()
        sock.sendall(length_str + encoded_command)

        length_data = b''
        while len(length_data) < 10:
            more = sock.recv(10 - len(length_data))
            if not more:
                raise Exception("Connection closed while reading length header")
            length_data += more
        total_length = int(length_data.decode())

        data_received = b''
        while len(data_received) < total_length:
            chunk = sock.recv(min(512*1024, total_length - len(data_received)))
            if not chunk:
                break
            data_received += chunk

        hasil = json.loads(data_received.decode())
        logging.warning("data received from server:")
        return hasil
    except Exception as e:
        logging.warning(f"error during data receiving: {e}")
        return False

# === Command functions ===
def remote_list():
    command_str = "LIST"
    hasil = send_command(command_str)
    if hasil and hasil['status'] == 'OK':
        print("Daftar file:")
        for nmfile in hasil['data']:
            print(f"- {nmfile}")
        return True
    else:
        print("Gagal")
        return False

def remote_download(filename="", worker_id=None):
    command_str = f"GET {filename}"
    hasil = send_command(command_str)
    if hasil and hasil['status'] == 'OK':
        namafile = hasil['data_namafile']
        if worker_id is not None:
            root, ext = os.path.splitext(namafile)
            namafile = f"{root}_worker{worker_id}{ext}"
        isifile = base64.b64decode(hasil['data_file'])
        with open(namafile, 'wb') as fp:
            fp.write(isifile)
        return True
    else:
        print("Gagal")
        return False

def remote_upload(filename=""):
    try:
        with open(filename, 'rb') as fp:
            isifile = base64.b64encode(fp.read()).decode()
        command_str = f"UPLOAD {filename} {isifile}"
        hasil = send_command(command_str)
        if hasil and hasil['status'] == 'OK':
            print(hasil['data'])
            return True
        else:
            print("Gagal")
            return False
    except Exception as e:
        print(f"Upload error: {e}")
        return False

def remote_delete(filename=""):
    command_str = f"DELETE {filename}"
    hasil = send_command(command_str)
    if hasil and hasil['status'] == 'OK':
        print(hasil['data'])
        return True
    else:
        print("Gagal")
        return False

# === Stress test functions ===
def upload_worker(filename):
    start = time.time()
    success = remote_upload(filename)
    end = time.time()
    duration = end - start
    filesize = os.path.getsize(filename)
    throughput = filesize / duration if duration > 0 else 0
    return success, duration, throughput

def download_worker(filename, worker_id):
    start = time.time()
    success = remote_download(filename, worker_id=worker_id)
    end = time.time()
    local_filename = f"{os.path.splitext(filename)[0]}_worker{worker_id}{os.path.splitext(filename)[1]}"
    filesize = os.path.getsize(local_filename) if os.path.exists(local_filename) else 0
    duration = end - start
    throughput = filesize / duration if success and duration > 0 else 0
    return success, duration, throughput

def run_stress_test(task_type='upload', file_size=10, num_workers=5, use_process=False, label='Thread'):
    filename = f'{file_size}MB.zip'
    executor_cls = concurrent.futures.ProcessPoolExecutor if use_process else concurrent.futures.ThreadPoolExecutor
    label = 'ProcessPool' if use_process else 'ThreadPool'
    task_func = upload_worker if task_type == 'upload' else download_worker

    print(f"\nRunning {task_type.upper()} test with file size {file_size}MB and {num_workers} workers using {label}...")

    with executor_cls(max_workers=num_workers) as executor:
        if task_type == 'download':
            futures = [executor.submit(download_worker, filename, i+1) for i in range(num_workers)]
        elif task_type == 'upload':
            futures = [executor.submit(task_func, filename) for _ in range(num_workers)]
        elif task_type == 'list':
            futures = [executor.submit(remote_list) for _ in range(num_workers)]
            return
        else:
            logging.info(f"task tidak dikenali")
            return

        total_success = 0
        total_failed = 0
        total_duration = 0
        total_throughput = 0

        for future in concurrent.futures.as_completed(futures):
            try:
                success, duration, throughput = future.result()
                if success:
                    total_success += 1
                    total_duration += duration
                    total_throughput += throughput
                else:
                    total_failed += 1
            except Exception as e:
                print(f"Worker error: {e}")
                total_failed += 1

        avg_duration = total_duration / total_success if total_success else 0
        avg_throughput = total_throughput / total_success if total_success else 0

        print(f"\n=== STATS [{label}] ===")
        print(f"Success: {total_success}, Failed: {total_failed}")
        print(f"Average Duration per Client: {avg_duration:.2f} seconds")
        print(f"Average Throughput per Client: {avg_throughput:.2f} bytes/second\n")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="File Client CLI & Stress Tool")
    subparsers = parser.add_subparsers(dest='mode', required=True)

    # CLI commands
    cli_parser = subparsers.add_parser('cli', help='Run basic client commands')
    cli_parser.add_argument('--command', choices=['list', 'get', 'upload', 'delete'], required=True)
    cli_parser.add_argument('--file', help='Filename for get/upload/delete')

    # Stress test
    stress_parser = subparsers.add_parser('stress', help='Run stress test')
    stress_parser.add_argument('--task', choices=['upload', 'download', 'list'], required=True)
    stress_parser.add_argument('--size', type=int, choices=[10, 50, 100], required=True)
    stress_parser.add_argument('--workers', type=int, choices=[1, 5, 50], required=True)
    stress_parser.add_argument('--method', choices=['thread', 'process'], default='thread')

    args = parser.parse_args()

    if args.mode == 'cli':
        if args.command == 'list':
            remote_list()
        elif args.command == 'get' and args.file:
            remote_download(args.file)
        elif args.command == 'upload' and args.file:
            remote_upload(args.file)
        elif args.command == 'delete' and args.file:
            remote_delete(args.file)
        else:
            print("Perintah membutuhkan --file")
    elif args.mode == 'stress':
        run_stress_test(
            task_type=args.task,
            file_size=args.size,
            num_workers=args.workers,
            use_process=(args.method == 'process')
        )

