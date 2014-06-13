import boto.ec2
import os, sys
from s3_helper import *

def generate_manifest(metadata):
	manifest = ""
	for k in metadata:
		manifest = manifest + k + " : " + str(metadata[k]) + "\n"
	return manifest

def parse_executable(exec_str):
	tokens = exec_str.split(' ')
	inputs = {}
	try:
		for i in range(1,len(tokens)):
			current = tokens[i]
			if current.startswith('-'):
				inputs[current] = ""
				i += 1
				next = tokens[i]
				while next.startswith('-') is False:
					inputs[current] = inputs[current] + " " + next
					i += 1
					next = tokens[i]
				i -= 1
				inputs[current] = inputs[current].strip()
	except IndexError:
		pass

	files = []
	for k in inputs:
		if os.path.isfile(inputs[k]):
			files.append(inputs[k])

	return tokens[0], inputs, files

def parse_manifest(manifest):
	lines = manifest.split('\n')
	params = {}
	inputs = {}
	for l in lines:
		tokens = l.split(' : ')
		if tokens[0].startswith('-'):
			inputs[tokens[0]] = tokens[1]
		else:
			params[tokens[0]] = tokens[1]

	return params, inputs

def generate_launch_script(uuid, params, inputs, files):
	script = "#!/bin/bash\n"
	# Copy files from S3
	for f in files:
		script = script + "curl https://s3.amazonaws.com/gdouglas.cs.ucsb.edu.research_bucket/" + str(f.key) + " > " + str(f.key).strip(uuid).split("/files")[1] + "\n"

	script = script + params['executable'] + " "
	for p in inputs:
		script = script + p + " " + inputs[p] + " "

	script = script + "\n"
	
	return script

def get_output_size(path):
	if not path.endswith('/'):
		path += '/'

	size = 0
	files = [path]
	while len(files) is not 0:
		if os.path.isfile(files[0]):
			size += os.path.getsize(files[0])
		elif os.path.isdir(files[0]):
			if not files[0].endswith('/'):
				files[0] += '/'
			for f in os.listdir(files[0]):
				files.append(files[0] + f)
		files.remove(files[0])

	return size


class CloudTracker:
	def __init__(self, tracking_number='0'):
		print "Initialized CloudTracker instance with uuid " + tracking_number
		self.uuid = tracking_number

	def init_tracking(self):
		print "Initializing tracking..."
		ami_id = get_ami_id()
		instance_type = get_instance_type()
		region = get_region()
		data = { "ami_id" : ami_id, 
		         "instance_type" : instance_type,
		         "region" : region}
		manifest = generate_manifest(data)
		print "Manifest : " + manifest
		create_file("gdouglas.cs.ucsb.edu.research_bucket", self.uuid + "/manifest", manifest)

	def track_input(self, exec_str):
		print "Tracking inputs..."
		executable, inputs, files = parse_executable(exec_str)
		data = { "executable" : executable }
		manifest = generate_manifest(data)
		print manifest
		add_to_file("gdouglas.cs.ucsb.edu.research_bucket", self.uuid + "/manifest", manifest)
		manifest = generate_manifest(inputs)
		print manifest
		add_to_file("gdouglas.cs.ucsb.edu.research_bucket", self.uuid + "/manifest", manifest)
		print files
		for f in files:
			upload_file("gdouglas.cs.ucsb.edu.research_bucket", f, self.uuid + "/files/" + f.strip('/'))
		self.timer = datetime.now()

	def track_output(self, output_dir):
		print "Tracking outputs..."
		exec_time = (datetime.now() - self.timer).total_seconds()
		output_size = get_output_size(output_dir)
		data = { "output_dir" : output_dir, "exec_time" : exec_time, "output_size" : output_size }
		manifest = generate_manifest(data)
		print manifest
		add_to_file("gdouglas.cs.ucsb.edu.research_bucket", self.uuid + "/manifest", manifest)

	def run(self, uuid, access_key, secret_key):

		print "running job with uuid " + str(uuid)
		manifest = get_file("gdouglas.cs.ucsb.edu.research_bucket", str(uuid) + "/manifest", access_key, secret_key).get_contents_as_string()
		params, inputs = parse_manifest(manifest.strip())

		print "Connecting to " + params['region']
		conn = boto.ec2.connect_to_region(
			params['region'],
			aws_access_key_id=access_key,
			aws_secret_access_key=secret_key
		)

		files = get_all_files("gdouglas.cs.ucsb.edu.research_bucket", str(uuid) + "/files", access_key, secret_key)
		script = generate_launch_script(str(uuid), params, inputs, files)
		print script

		print "Launching worker from AMI: " + params['ami_id']
		rs = conn.run_instances(
			params['ami_id'],
			instance_type=params['instance_type'],
			security_groups=['default-ssh'],
			user_data=script
		)

		inst = rs.instances[0]
		while inst.state != 'running':
			inst.update()

		print "Finished"
