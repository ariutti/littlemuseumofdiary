"""
La classe gestisce il player video, questo può essere OMX o VLC a seconda dei casi.
AL momento l'implementazione corretta di OMX non è ancora correttamente funzionante,
c'è ancora un po' da lavorarci.
"""

import time, re
import subprocess as sp
from omxplayer.player import OMXPlayer
import vlc, mouse

class VideoPlayer:

	def __init__(self, VIDEO_NAME, IMAGE_WIDTH, IMAGE_HEIGHT, USING_VLC = False, audioPlayerRef=None, pygameRef=None):

		self.USING_VLC = USING_VLC
		self.VIDEO_FILE = VIDEO_NAME
		#get a reference to the audio player
		self.audioPlayerRef = audioPlayerRef

		self.player = None

		if self.USING_VLC:
			if( pygameRef == None):
				print("VIDEOPLAYER ERROR: don't have a reference to pygame window!")

			self.vlcInstance = vlc.Instance()
			#tmp (remove comment here) self.media = self.vlcInstance.media_new('/home/pi/code/' + self.VIDEO_FILE)
			self.media = self.vlcInstance.media_new(self.VIDEO_FILE)

			# Create new instance of vlc player
			self.player = self.vlcInstance.media_player_new()
			self.player.stop()

			# Pass pygame window id to vlc player, so it can render its contents there.
			win_id = pygameRef.display.get_wm_info()['window']
			self.player.set_xwindow(win_id)
			self.player.set_media(self.media)

			# TODO: correct the line below
			mouse.move(IMAGE_WIDTH, IMAGE_HEIGHT, True, 0)
		else:
			self.omx_stdin = None
			self.omx_process = None
			self.tot_sec = None

		self.STARTED = False
		self.PAUSED  = False
		if( self.USING_VLC ):
			print("VIDEOPLAYER: using VLC" )
		else:
			print("VIDEOPLAYER: using OMX" )

		# info about video
		self.info_video = {}
		self.chapters = self.get_chapters()
		self.curr_chapter = 0
		print('VIDEOPLAYER: info video \n\t# chapter:{}\n\t{}'.format(len(self.chapters), self.chapters) )

	def start(self):
		print("VIDEOPLAYER: Starting video...")
		self.STARTED = True
		self.PAUSED = False

		if self.USING_VLC:
			self.player.play()
		else:
			if self.player:
				self.player.quit()
				self.player = None
			self.player = OMXPlayer(self.VIDEO_FILE, args=['--no-osd'])
		time.sleep(1)

	def stop(self):
		print("VIDEOPLAYER: Stopping video...")
		self.STARTED = False
		#TODO: is it necessary
		#self.PAUSED = True
		if self.USING_VLC:
			self.player.stop()
		else:
			self.player.quit()
			self.player = None

	def pause(self):
		print("VIDEOPLAYER: Pausing video...")
		# TODO: add some code here??
		#self.PAUSED = True #??

	def needUpdate(self):
		return (self.STARTED and self.player)
		
	def update(self):
		#print("VIDEOPLAYER: update")
		if self.USING_VLC:
			if  self.player.get_length() - self.player.get_time() < 2000 and not self.PAUSED:
				print("VIDEOPLAYER VLC: a due secondi dalla fine")
				self.PAUSED = True
				self.player.set_pause(1)
		else:
			if  self.player.duration() - self.player.position() < 2 and not self.PAUSED:
				print('VIDEOPLAYER OMX: a due secondi dalla fine')
				self.PAUSED = True
				self.player.pause()
		#self.printStatus()

	def printStatus(self):
		print("VIDEOPLAYER: started {}, paused {}".format(self.STARTED, self.PAUSED ) )

	def changeChapter(self, chapter):
		print("VIDEOPLAYER: change chapter") 
		if chapter != 0:
			print("VIDEOPLAYER: chapter != 0") 
			# in origin era così riga commentata)
			#if self.PAUSED == True:
			#if self.PAUSED == False:
			#print("VIDEOPLAYER: paused is true")
			if self.USING_VLC:
				self.player.set_pause(0)
			else:
				if self.player:
					self.player.play()
			self.PAUSED = False
				
			if self.USING_VLC:
				self.handle_chapter_vlc(chapter)
			else:
				self.handle_chapter_omx(chapter)
		"""
		if self.USING_VLC:
			if  self.player.get_length() - self.player.get_time() < 2000 and not self.PAUSED:
				self.PAUSED = True
				self.player.set_pause(1)
		else:
			if  self.player.duration() - self.player.position() < 2 and not self.PAUSED:
				print('...pausing video')
				self.PAUSED = True
				self.player.pause()
				
		"""
		"""
		#not using language right now
		# return to italian language
		if self.audioPlayerRef:
			self.audioPlayerRef.switchToITA()
		"""

	def isPlaying(self):
		return self.STARTED

	def switch_language(self):
		print("Video: switch language...")
		if self.audioPlayerRef:
			self.audioPlayerRef.switchLanguage()
		if self.player:
			self.player.set_position(0)

	# get all chapters of video file
	def get_chapters(self):
		buff = sp.check_output(["ffmpeg", "-i", self.VIDEO_FILE, "-f",'ffmetadata', "file.txt", '-y'], stderr=sp.STDOUT, universal_newlines=True)
		#print(buff)
		self.chapters = []
		self.chapters_info = {}
		names = []
		i = 0
		for line in iter(buff.splitlines()):
			m = re.match(r".*Chapter #(\d+:\d+): start (\d+\.\d+), end (\d+\.\d+).*", line)
			if m != None and m.group(1) not in names:
				names.append(m.group(1))
				self.chapters.append({ "name": i + 1, "start": float(m.group(2)), "end": float(m.group(3))})
				i = i + 1
		if len(self.chapters) == 2:
			self.chapters[len(self.chapters) - 1]['name'] = 3
		return self.chapters

	# check where i am:
	# 0: before chapter 1
	# 1: chapter 1
	# 2: chapter 2
	# 3: chapter 3
	# 10 last chapter
	def pos2chapter(self, pos):
		# ~ print('actual position', pos)
		for x in self.chapters:
			if pos >= x['start'] / 1000 and pos <= x['end']:
				return x['name']
		if pos < self.chapters[0]['start']:
			return 0
		if pos > self.chapters[len(self.chapters) - 1]['end']:
			return self.chapters[len(self.chapters) - 1]['name']

	# vlc chapter manager
	def handle_chapter_vlc(self, c):
		print('VIDEOPLAYER VLC: going to', len(self.chapters), c)
		if len(self.chapters) == 2:
			if c == 3:
				print(1)
				self.player.set_chapter(1)
			if c == 1:
				print(2)
				self.player.set_chapter(0)
		else:
			self.player.set_chapter(c - 1)
		self.audioPlayerRef.stop()
		if c == 1:
			self.audioPlayerRef.start()
		self.curr_chapter = c

	# chapter manager
	def handle_chapter_omx(self, c):
		self.curr_chapter = self.pos2chapter(self.player.position())
		print('VIDEOPLAYER OMX: Handle chapter: from', self.curr_chapter, 'to', c)
		# ~ if c != curr_chapter and c in [f['name'] for f in chapters]:
		if c in [f['name'] for f in self.chapters]:
			cpt = self.chapters[[y for y, x in enumerate(self.chapters) if x['name'] == c][0]]
			time.sleep(1)
			print('going to', cpt['start'])
			self.player.set_position(cpt['start'])
			time.sleep(1)
			self.audioPlayerRef.stop()
			if c == 1:
				self.audioPlayerRef.start()
			self.curr_chapter = c

	def kill(self):
		print("Kill video...")
		if self.USING_VLC:
			self.player.stop()
		else:
			self.player.quit()
			self.player = None
