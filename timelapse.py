import os
import sys
import shutil
import commands
from datetime import datetime
from picamera import PiCamera
from time import sleep

from googledrive import GoogleDriveManager

# Always expand current dir to a full directory instead of using relative directory.
CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))


def make_video_from_images(images_dir, output_dir, images_count=None, upload_video_to_gdrive=False):
	"""
	Run FFMPEG with dir of images, output dir, and maximum number of images
	Stitch all pictures together to make a time lapse video
	:param images_dir: Image directory
	:param output_dir: Output directory
	:param images_count: Number of images in total
	:param upload_video_to_gdrive: Bool. To be uploaded to google drive or not.
	"""
	FRAME_RATE = 30

	# Too little images, set FRAME_RATE to the exactly number of images
	if images_count:
		if images_count < FRAME_RATE:
			FRAME_RATE = images_count

	# Run ffmpeg to generate timelapse.mp4
	cmd = 'ffmpeg -r {} -i {} -c:v libx264 -vf fps=25 -pix_fmt yuv420p {}'.format(
		FRAME_RATE,
		images_dir + 'image%d.jpeg',
		output_dir + '/timelapse.mp4'
	)

	print('Generating timelapse.mp4, please wait...')

	(status, output) = commands.getstatusoutput(cmd)
	if status != 0:
		print('Error running: \n' + cmd)
		print '\n\n' + output
		sys.exit(1)

	else:
		# Everything working fine
		# Flush data to sd card to prevent data loss.
		commands.getstatusoutput('sync')

		print('All done! timelapse.mp4 is saved in ' + output_dir + '/timelapse.mp4')

		if upload_video_to_gdrive:
			drive_manager = GoogleDriveManager()

			# Upload video to google drive.
			print('Attempting to upload to google drive...')

			ufile = (output_dir + '/timelapse.mp4', 'video/mp4')
			result = drive_manager.upload_file(ufile, folder_name='timelapse')
			if result.get('name'):
				print('Successfully uploaded {} to google drive.'.format(result.get('name')))

		# Delete images from local directory to save space
		shutil.rmtree(images_dir)


def timelapse_loop(duration, interval, pi_camera, save_to_googledrive, autoloop=False):
	# Camera setup
	camera = pi_camera

	# Eg. 2014-10-02T05:10:25.642155 (year, month, day, hours, minutes, seconds, microseconds)
	created_timestamp = datetime.now().isoformat()
	TIMELAPSE_DIR = CURRENT_DIR + '/' + created_timestamp
	IMAGES_DIR = TIMELAPSE_DIR + '/images/'

	# Create dir if not already exist
	if not os.path.exists(TIMELAPSE_DIR):
		os.mkdir(TIMELAPSE_DIR)

	# Create an 'images' folder inside
	if not os.path.exists(IMAGES_DIR):
		os.mkdir(IMAGES_DIR)

	# Options for generating time lapse video

	# Get max number of images to find out when to stop recording
	max_count = (duration * 60) / interval
	# Used for name of image
	count = 0

	# Setup exit handler. (Automatically stitch videos if exit)
	import signal

	def handle_exit(signum=None, frame=None):
		print('\nAll images saved in ' + IMAGES_DIR)

		if save_to_googledrive:
			make_video_from_images(images_dir=IMAGES_DIR, output_dir=TIMELAPSE_DIR, images_count=count,
								upload_video_to_gdrive=True)
		else:
			make_video_from_images(images_dir=IMAGES_DIR, output_dir=TIMELAPSE_DIR, images_count=count,
								upload_video_to_gdrive=False)

	signal.signal(signal.SIGTERM, handle_exit)
	signal.signal(signal.SIGINT, handle_exit)

	print('Timelapse running for {} minutes at 1 frames per {} second(s)'.format(duration, interval))
	print('Taking pictures for time lapse...')
	print('timelapse.py is running with PID of:' + str(os.getpid()))
	print('If CTRL-C does not work, use pkill {PID} to quit and save time lapse.')

	# Increment every 1 percentage.
	percentage = 0.01
	while count < max_count:
		# Give an output for every 1%++ of the video.
		if count + 1 / max_count == 1:
			print('{}% completed. ({}/{})'.format(100, count, max_count))
		elif count / max_count >= percentage:
			print('{}% completed. ({}/{})'.format(int(count / max_count * 100), count, max_count))
			percentage = count / max_count * 0.01

		# All files will be saved in folder according to their date.
		camera.capture(IMAGES_DIR + 'image' + str(count) + '.jpeg')
		count += 1
		sleep(interval)

	if count >= max_count:
		# Only run autoloop if current loop finished naturally. DOES NOT RUN if script is interrupted or killed
		# Note: handle_exit() will be called automatically, so theres no need to call make_video()
		if autoloop:
			print("Stopping camera...")
			camera.close()

			# Create path to log if not available.
			logs_path = CURRENT_DIR + '/logs'
			if not os.path.exists(logs_path):
				os.mkdir(logs_path)

			os.system('python {} > {} &'.format(os.path.join(CURRENT_DIR, 'autotimelapse.py'),
												'{}/{}LOG.txt'.format(logs_path, created_timestamp)
												))


def main():
	print('TIME-LAPSE')
	print('CTRL-C to save time lapse video and exit.')

	# Setup exit handler in the case the python script is terminated.

	duration = raw_input('Enter duration of capture in minutes (leaving empty defaults to 1440 minutes [24 hours])\n: ')
	interval = raw_input('Enter interval per capture in seconds (leaving empty defaults to 5 seconds per capture)\n: ')

	# Default value for duration and interval
	try:
		duration = int(duration)
	except ValueError:
		duration = 1440
	try:
		interval = int(interval)
	except ValueError:
		interval = 5

	# Additional camera setup
	pi_camera = PiCamera()
	pi_camera.resolution = (1024, 768)
	print (type(pi_camera.resolution))
	timelapse_loop(interval=interval, duration=duration, pi_camera=pi_camera, save_to_googledrive=True)


if __name__ == '__main__':
	main()
