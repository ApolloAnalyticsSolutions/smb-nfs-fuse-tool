import psutil
import time
import os
import logging
import tempfile
import json
import subprocess

# Set up logging
logging.basicConfig(filename='logs/performance_analyzer.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')  # Fixed PEP8 compliance: line length

def load_config(config_file="config.json"):
    """
    Load configuration from a JSON file.
    """
    try:
        with open(config_file) as f:
            config = json.load(f)
        logging.info("Successfully loaded configuration file.")
        return config
    except FileNotFoundError:
        logging.error("Configuration file 'config.json' not found.")
        raise

def analyze_file_system_cache():
    """
    Analyze file system cache usage.
    """
    vm = psutil.virtual_memory()
    result = {}

    if 'cached' in vm._fields:
        result["cached_memory"] = vm.cached

    if vm.available:
        result["available_memory"] = vm.available

    if vm.total:
        result["total_memory"] = vm.total

    if vm.used:
        result["used_memory"] = vm.used

    if vm.percent:
        result["percent_used"] = vm.percent

    return result

def test_network_throughput(server, export_path):
    """
    Test network throughput by copying a file to and from the NFS server.
    """
    with tempfile.NamedTemporaryFile(delete=False) as tmpfile:
        test_file = tmpfile.name
        test_file_size = 100 * 1024 * 1024  # 100 MB test file

        remote_file = os.path.join(export_path, os.path.basename(test_file))
        try:
            with open(remote_file, 'wb') as f:
                f.write(os.urandom(test_file_size))

            start_time = time.time()
            subprocess.run(["cp", remote_file, test_file], check=True)
            end_time = time.time()

            duration = end_time - start_time
            throughput = (test_file_size / duration) / (1024 * 1024)  # MB/s
            return throughput

        except subprocess.CalledProcessError as e:
            logging.error(f"Network throughput test copy failed: {e}")
            return None

        finally:
            try:
                os.remove(test_file)
                os.remove(remote_file)
            except Exception as e:
                logging.warning(f"Error cleaning up test files: {e}")

def get_network_stats(interface="eth0"):
    """
    Get network statistics for a specific interface.
    """
    net_io = psutil.net_io_counters(pernic=True)
    stats = net_io.get(interface)
    result = {}

    if stats:
        if stats.bytes_sent is not None:
            result["bytes_sent"] = stats.bytes_sent
        if stats.bytes_recv is not None:
            result["bytes_recv"] = stats.bytes_recv
        if stats.packets_sent is not None:
            result["packets_sent"] = stats.packets_sent
        if stats.packets_recv is not None:
            result["packets_recv"] = stats.packets_recv

        return result
    else:
        return None

def generate_performance_report(config_file='config.json'):
    """
    Generate a performance report based on the configuration file.
    """
    print("Generating performance report...")
    config = load_config(config_file)

    # Analyze file system cache
    cache_usage = analyze_file_system_cache()
    nfs_default_server = config.get("nfs_default_server", "localhost")
    nfs_default_export_path = config.get("nfs_default_export_path", "/var/www/nfs_export/")

    # Test network throughput (NFS)
    nfs_throughput = test_network_throughput(nfs_default_server, nfs_default_export_path)

    # Output the results
    print("File System Cache Usage:", json.dumps(cache_usage, indent=4))
    print(f"NFS Throughput: {nfs_throughput} MB/s")

if __name__ == '__main__':
    generate_performance_report()
