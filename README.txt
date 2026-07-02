# Network Performance Tool

The Network Performance Tool is a Python package designed to analyze and optimize the performance of network file systems, specifically SMB and NFS shares. It provides utilities to gather settings, measure throughput, and generate recommendations for tuning.

## Features

- **SMB Analysis**: Collects and analyzes settings and performance metrics for SMB shares.
- **NFS Analysis**: Gathers mount options, server settings, and performance data for NFS shares.
- **Performance Reporting**: Generates a comprehensive report on file system cache usage, network statistics, and network throughput.
- **Recommendations**: Suggests configuration changes to improve performance based on machine learning analysis and collected data.

## Installation

To install the nfs-smb-util, ensure you have Python 3.6 or later and pip installed. Then, run the following command:
Download the Package:
Download the package files, including setup.py and the src directory, to a local directory on your computer.

Create a Virtual Environment (Optional):
It's a good practice to create a virtual environment for your Python projects to avoid conflicts between dependencies. You can create a virtual environment using the following command:

`python -m venv venv`

Activate the virtual environment:

On Windows:

`venv\Scripts\activate`

On macOS and Linux:

`source venv/bin/activate`

Install the Package:
Navigate to the directory where you downloaded the package and run the following command to install it:

`pip install .`

## Usage

### Console Scripts

The package provides several console scripts for easy access to its functionalities:

- **`network_tool`**: Runs the main analysis workflow, including SMB and NFS information gathering, performance analysis, and recommendations generation.

  Usage: `network_tool`

- **`smb_analysis`**: Performs an analysis specifically for SMB shares, collecting settings and performance data.

  Usage: `smb_analysis`

- **`nfs_analysis`**: Focuses on NFS shares, gathering mount options, server settings, and performance metrics.

  Usage: `nfs_analysis`

- **`performance_report`**: Generates a detailed performance report, including file system cache usage, network statistics, and throughput analysis.

  Usage: `performance_report`

### Python API

You can also use the Network Performance Tool programmatically within your Python scripts:

pythonCopy code

`from network_performance_tool import smb_utils, nfs_utils, performance_analyzer

# Run SMB analysis

smb_info = smb_utils.run_smb_analysis()

# Run NFS analysis

nfs_info = nfs_utils.run_nfs_analysis()

# Generate a performance report

performance_report = performance_analyzer.generate_performance_report()`

## Configuration

The tool relies on a `config.json` file for configuration settings. This file should be located in the root directory of your project and include the following keys:

`{
  "fuse": {
      "root": "/mnt/fuse_test",
      "mount_options": {
          "allow_other": true,
          "default_permissions": true
      }
  },
  "smb_default_server": "smb_server",
  "smb_default_share": "smb_share",
  "smb_username": "smb_user",
  "smb_password": "smb_pass",
  "nfs_default_server": "nfs_server",
  "nfs_default_export_path": "/nfs_export",
  "network_interface": "eth0"
}`

## Modules

1. Configuration (config.json)
   The config.json file contains the configuration settings for the package. It includes settings for FUSE (Filesystem in Userspace), SMB (Server Message Block), NFS (Network File System), and the network interface.

   - FUSE: Used for mounting file systems in user space. The root specifies the mount point, and mount_options provides additional options like allow_other and default_permissions.
   - SMB: Configuration for SMB server, share, username, and password.
   - NFS: Settings for NFS server and export path.
   - Network Interface: Specifies the network interface to use (e.g., eth0). 2. Package Setup (setup.py)
   - The setup.py file is used to package and distribute the Python package. It includes the package name, version, package directory, dependencies, and entry points for console scripts.
   - Dependencies: Lists the required Python packages like fusepy, pandas, scikit-learn, paramiko, psutil, and smbprotocol.
   - Entry Points: Defines console scripts for various utilities like network_tool, smb_analysis, nfs_analysis, and performance_report.

2. FUSE Integration (fuse_integration.py)This module handles the integration with the FUSE filesystem. It would include code to mount, unmount, and interact with the filesystem using the FUSE library.
   This module handles the integration with FUSE (Filesystem in Userspace), allowing the package to mount file systems in user space. Key functionalities might include:

   - Mounting: Functions to mount a file system using FUSE.
   - Unmounting: Functions to unmount a previously mounted file system.
     File System Operations: Implementations of file system operations like read, write, and list directory, which are required by FUSE.

3. Machine Learning (machine_learning.py)
   This module contain a basic machine learning models or algorithms used for analysis or recommendations within the package. It could include code for training models, making predictions, and evaluating performance.
   This module is expected to contain machine learning algorithms or models used for analysis or recommendations. It include:

   - Model Training: Code to train machine learning models on data.
   - Prediction: Functions to make predictions using trained models.
   - Evaluation: Code to evaluate the performance of the models.

4. Main Module (main.py)
   The main.py module is the entry point for the network_tool console script. It likely contains the main logic for running the network performance tool, handling command-line arguments, and coordinating other modules.
   The main.py module is the entry point for the network tool. It likely orchestrates the overall functionality of the package, including:

   - Argument Parsing: Code to parse command-line arguments.
   - Module Coordination: Logic to call functions from other modules based on user input.
   - Output: Handling the output of the tool, such as displaying results or generating reports.

5. NFS Utilities (nfs_utils.py)
   This module contains utilities for working with NFS. It might include functions for connecting to NFS servers, transferring files, and analyzing NFS performance.
   This module contains utilities for working with NFS (Network File System). It might include:

   - NFS Connection: Functions to connect to an NFS server.
   - File Operations: Code to perform file operations like read, write, and copy over NFS.
   - Performance Analysis: Utilities to analyze the performance of NFS, such as measuring transfer speeds or latency.

6. Performance Analyzer (performance_analyzer.py)
   The performance_analyzer module is responsible for generating performance reports. It could include code for collecting performance metrics, analyzing data, and generating reports.
   The performance_analyzer module is responsible for analyzing network performance. It could include:

   - Data Collection: Code to collect performance metrics, such as bandwidth usage, latency, and error rates.
   - Analysis: Functions to analyze the collected data, identify bottlenecks or issues, and provide insights.

7. Recommendations (recommendations.py)
   This module might provide recommendations based on the analysis performed by the package. It could include code for generating recommendations based on machine learning models or heuristic algorithms.
   This module likely provides recommendations based on the analysis performed by the package. It could include:

   - Recommendation Engine: Code to generate recommendations, which could be based on machine learning models or heuristic algorithms.
   - Output: Functions to present the recommendations to the user, possibly with explanations or justifications.

8. SMB Utilities (smb_utils.py)
   Similar to nfs_utils.py, this module contains utilities for working with SMB. It might include functions for connecting to SMB shares, file operations, and SMB performance analysis.
   Similar to nfs_utils.py, this module contains utilities for working with SMB (Server Message Block). It include:

   - SMB Connection: Functions to connect to an SMB share.
   - File Operations: Code to perform file operations like read, write, and copy over SMB.
   - Performance Analysis: Utilities to analyze the performance of SMB, such as measuring transfer speeds or latency.

9. Stress Test (stress_test.py)
   The stress_test.py module likely contains code for stress testing the network or file systems. It could include functions for generating heavy load and measuring system performance under stress.
   The stress_test.py module likely contains code for stress testing the network or file systems. It could include:

   - Load Generation: Functions to generate heavy load on the network or file systems.
   - Performance Monitoring: Code to monitor the system performance under stress, measuring metrics like throughput and response time.
   - Report Generation: Utilities to generate reports on the stress test results, highlighting any weaknesses or bottlenecks.

## Development

To set up a development environment for the Network Performance Tool:

1. Clone the repository.
2. Install the dependencies: `pip install -r requirements.txt`.
3. Make changes to the source code.
4. Run tests to ensure everything is working as expected.

## Contributing

Contributions to the Network Performance Tool are welcome! Please follow these steps to contribute:

1. Fork the repository.
2. Create a new feature branch.
3. Make your changes and add tests.
4. Submit a pull request with a description of your changes.

## License

The Network Performance Tool is released under the MIT License.

