import json
import logging

logging.basicConfig(filename='logs/recommendations.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')  # Added logging configuration

def suggest_nfs_tuning(nfs_settings, nfs_server_settings, nfs_performance_data):
    """
    Suggest NFS tuning recommendations based on current settings and performance data.
    """
    recs = []

    if "ro" not in nfs_settings:
        recs.append(
            "Consider adding the 'ro' mount option for potential performance gains (if the workload is read-heavy)")

    if "async" not in nfs_settings:
        recs.append(
            "Consider adding 'async' for improved performance if your workload allows it.")

    if nfs_performance_data.get("cached_memory"):  # Check if data exists
        cached_memory_mb = nfs_performance_data["cached_memory"] / (1024 * 1024)
        if cached_memory_mb < 200:
            recs.append("Increase system RAM to improve file system caching.")
    else:
        logging.warning("Cached memory data unavailable for NFS recommendations.")

    if "insecure" in nfs_server_settings:
        recs.append(
            "Consider removing the 'insecure' export option on the NFS server for enhanced security (if possible).")

    return recs

def load_optimization_settings(settings_file="optimization_settings.json"):
    """
    Load optimization settings from a JSON file.
    """
    try:
        with open(settings_file) as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error("Optimization settings file not found.")
        return {}

def suggest_smb_tuning(smb_settings, smb_server_settings, smb_performance_data):
    """
    Suggest SMB tuning recommendations based on current settings and performance data.
    """
    recs = []

    optimization_settings = load_optimization_settings()

    if "rsize" in smb_settings:
        try:
            current_rsize = int(smb_settings.split("rsize=")[-1])  # Extract value
            if current_rsize < 65536:
                recs.append(
                    "Increase 'rsize' for potentially better read performance (consider testing with larger values).")
        except ValueError:
            logging.warning("Invalid rsize value found in smb_settings.")

    if "socket options" not in smb_server_settings:
        recs.append(
            "Consider adding 'socket options' on the SMB server for potential optimizations (refer to Samba documentation).")

    return recs
