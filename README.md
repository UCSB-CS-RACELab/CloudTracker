CloudTracker
============

Provenance Tracking for Data Reproduction

cloudtracker.py contains the CloudTracker class that can be imported into a job management system.
s3_helper.py contains many helpful functions that CloudTracker uses to interact with Amazon S3

The following library calls can be used to perform provenance tracking:

init_tracking()

track_input(exec_string)

track_output(output_dir)

The following function can be used to run a replay of a previously finished job:

run(uuid,access_key,secret_key)