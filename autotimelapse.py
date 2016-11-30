from picamera import PiCamera
import timelapse
import ConfigParser
import os

config_parser = ConfigParser.RawConfigParser()
# Get the absolute path. Because doesn't work if it is run from a different directory (not cwd)
config_file = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'config.txt')
config_parser.read(config_file)

print('Using settings from ' + config_file)

# Duration and interval is from config.txt
duration = config_parser.get('Capture Options', 'duration').replace(' ', '')
interval = config_parser.get('Capture Options', 'interval_per_capture').replace(' ', '')

# Strip comments if available
if '#' in duration:
	duration, comment = duration.split('#')
if '#' in interval:
	interval, comment = interval.split('#')

# Camera
camera = PiCamera()
resolution = config_parser.get('Camera Options', 'resolution').replace(' ', '')
if '#' in resolution:
	resolution, comment = resolution.split('#')

# Resolution in this format '1080x768'
resolution = resolution.split('x')
camera.resolution = (int(resolution[0]), int(resolution[1]))

# Other options
save_to_googledrive = config_parser.get('Others', 'save_to_googledrive').replace(' ', '')
if save_to_googledrive and save_to_googledrive.lower() == 'true':
	save_to_googledrive = True
else:
	save_to_googledrive = False

autoloop = config_parser.get('Others', 'autoloop').replace(' ', '')

if '#' in autoloop:
	autoloop, comment = autoloop.split('#')

if autoloop and autoloop.lower() == 'true':
	autoloop = True
else:
	autoloop = False

# Run timelapse
timelapse.timelapse_loop(float(duration), float(interval), camera, save_to_googledrive, autoloop=autoloop)
