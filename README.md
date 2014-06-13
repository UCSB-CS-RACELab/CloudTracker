CloudTracker
============

Provenance Tracking for Data Reproduction

CloudTracker library functions can be incorporated into any job management system that meets the following constraints:

Job Manager assigns UUIDs to jobs

Job Manager deploys job to Amazon EC2 with a specific execution string that contains an executable name and input parameters supplied via the command line

Inputs are key-value pairs, boolean parameters, or input files (absolute filepath)

Ouputs are files and are stored in a specificied output directory


Using CloudTracker
=================

Provenance Tracking
```python
from cloudtracker import CloudTracker

# Instantiate new CloudTracker object with the UUID of a job to track
ct = CloudTracker(uuid)

# Initiate data provenance tracking, records environmental information
ct.init_tracking()

# Record job inputs from the exec_string
ct.track_input(exec_string)

# Record location of output directory. Also record total running time and size of results
ct.track_output(output_dir)
```

Data Reproduction
```python
from cloudTracker import CloudTracker

# Instantiate new CloudTracker object, no UUID required
ct = CloudTracker()

# Replay a job with the specified uuid. Credentials used to allocate cloud resources
ct.run(uuid, access_key, secret_key)
```
