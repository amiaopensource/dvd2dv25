#!/usr/bin/env python
import argparse
import os
import subprocess
import sys

# This code block binds
# raw_input() to input() 
# so that the script is Pyton 2.7 compatible
######################
try:
    input = raw_input
except NameError:
    pass
######################

def set_args():
	parser = argparse.ArgumentParser()
	parser.add_argument(
		'-o', '--outputPath',
		help='path where you want the output ISO file to live'
	)
	return parser.parse_args()


def get_devs():
	'''
	List all the disks mounted at /dev and return a dict showing them all
	We will ask the user which one(s?) they want to run `ddrescue` on.
	'''

	# init a dict of mount points on /dev
	availableDevPoints = {}
	# init a counter that will be used to select the volume(s) we want
	devPointCounter = 1
	# run `df` to see what's up on the system
	dfProcess = subprocess.Popen(['df'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	out, err = dfProcess.communicate()

	dfLines = [
		line.decode() for line in out.splitlines()
		if '/dev/disk' in line.decode()
	]
	for line in dfLines:
		mountPoint = line.split()[0]
		humanName = line.split()[8]
		if humanName.split('/')[-1] == '':
			pass
		else:
			availableDevPoints[devPointCounter] = {}
			availableDevPoints[devPointCounter][mountPoint] = humanName.split('/')[-1]
			devPointCounter += 1

	# print(availableDevPoints)
	return availableDevPoints


def ask_which_mount(availableDevPoints):
	print("here are the mounted volumes on the system:")
	for key, value in availableDevPoints.items():
		for k, v in value.items():
			print("NUMBER: {} ... Actual Name: {}".format(key, v))
	selection = str(
		input(
			"Please enter the NUMBER for the volumes " \
			"you want to rip. Separate multiple selections " \
			"with a comma (eg 1,2): "
			)
		)
	if len(selection) > 1:
		try:
			selections = [
				int(number.rstrip()) for number in selection.split(',')
			]
		except:
			print("your selection ({}) was not understood. Try again! " \
				  "Next time separate numbers with a comma, like so: 1,2,3")
			sys.exit()
		if not all(
				choice in list(availableDevPoints.keys()) for choice in selections
		):
			print("your choice(s) ({}) " \
				  "include invalid selections. Try again.".format(selections))
			sys.exit()
		else:
			pass

	else:
		selections = selection

	print(selections)
	return (selections)


def unmount_volume(volume):
	umountStatus = False
	message = ''
	command = ["diskutil", "umount", volume]
	process = subprocess.Popen(
		command, 
		stdout=subprocess.PIPE, 
		stderr=subprocess.PIPE
		)
	out, err = process.communicate()

	if not err.decode() == '':
		message = err
	else:
		umountStatus = True

	return umountStatus, message


def run_ddrescue(ddrescuePath, selections, availableDevPoints, outputPath):
	for volume in selections:
		mountDetails = availableDevPoints[int(volume)]
		mountPath = list(mountDetails.keys())[0]
		mountHuman = mountDetails[mountPath]
		isoPath = os.path.join(outputPath, mountHuman + ".iso")
		logPath = isoPath + ".log"
		umountStatus, message = unmount_volume(mountPath)
		if not umountStatus:
			print("unmounting got this error: {}".format(message.decode()))
		else:
			ddrescueCommand = [
				"ddrescue",
				"-b", "2048",
				"-v",
				mountPath,
				isoPath,
				logPath
			]
			process = subprocess.Popen(
				ddrescueCommand,
				stdout=subprocess.PIPE,
				stderr=subprocess.PIPE
			)
			out, err = process.communicate()
			availableDevPoints[int(volume)]['status'] = "{} | {}".format(out, err)
	return availableDevPoints


def check_ddrescue():
	out = subprocess.Popen(['which', 'ddrescue'], stdout=subprocess.PIPE)
	out.communicate()
	if not out.stdout == '':
		return out.stdout
	else:
		return False

def eject_disc():
	out = subprocess.Popen(['drutil', 'eject'], stdout=subprocess.PIPE)
	out.communicate()

def main():
	args = set_args()
	outputPath = args.outputPath
	if not outputPath:
		outputPath = input("Please drag in a folder " \
			"where you want your output to live:")
	outputPath = outputPath.rstrip()
	if not os.path.isdir(outputPath):
		print("your output path is bunk. try again.")
		sys.exit()

	ddrescuePath = check_ddrescue()
	if not ddrescuePath:
		print("Buddy, you gotta install ddrescue. Come back later!")
		sys.exit()

	availableDevPoints = get_devs()
	selections = ask_which_mount(availableDevPoints)
	ripStatus = run_ddrescue(
		ddrescuePath,
		selections,
		availableDevPoints,
		outputPath
	)
	eject_disc()
	for key, value in ripStatus.items():
		# print(value)
		print(ripStatus[key]['status'])


if __name__ == '__main__':
	main()