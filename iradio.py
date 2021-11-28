#!/usr/bin/python
#
# Internet radio
# Raspberry Pi
#
# Author : Dovydas Rusinskas
# Site	 : http://www.electronic.lt
#
# Date	 : 2017 05 28
# Version: 1.7
 
# The wiring for the LCD is as follows:
# 1 : GND
# 2 : 5V
# 3 : Contrast (0-5V)*
# 4 : RS (Register Select)
# 5 : R/W (Read Write)			 - GROUND THIS PIN
# 6 : Enable or Strobe
# 7 : Data Bit 0						 - NOT USED
# 8 : Data Bit 1						 - NOT USED
# 9 : Data Bit 2						 - NOT USED
# 10: Data Bit 3						 - NOT USED
# 11: Data Bit 4
# 12: Data Bit 5
# 13: Data Bit 6
# 14: Data Bit 7
# 15: LCD Backlight +5V**
# 16: LCD Backlight GND
 
#import
import RPi.GPIO as GPIO
import time
import mpd 
import re
import os
import requests
import threading

MPD_SERVER_IP_HOST = "localhost"
MPD_SERVER_PORT = 6600
MPD_SERVER_PASSWORD = "" #not implemented/tested

DISPLAY_TYPE = "LCD_HD44780" #LCD_HD44780 or OLED_WS0010


# Define GPIO to LCD mapping
LCD_RS = 7
LCD_E	= 8
LCD_D4 = 25
LCD_D5 = 24
LCD_D6 = 23
LCD_D7 = 18
 
# Define some device constants
LCD_WIDTH = 16	# Maximum characters per line
LCD_CHR = True
LCD_CMD = False
 
LCD_LINE_1 = 0x80 # LCD RAM address for the 1st line
LCD_LINE_2 = 0xC0 # LCD RAM address for the 2nd line
 
# Timing constants
#E_PULSE = 0.00005
#E_DELAY = 0.00005
E_PULSE = 0.00007
E_DELAY = 0.00007

BTN_RIGHT = 10
BTN_MENU = 11
BTN_LEFT = 9

mpd_client = mpd.MPDClient()		# global Init MPD mpd_client

song_num = 0
mpd_status_songid = 0
mpd_status_playlistlength = 0
update_flag = 0	

oled_saving = 0
OLED_TIMEOUT = 3 *60 *60 #in seconds
oled_timeout_counter = OLED_TIMEOUT

def my_callback(channel):

	global song_num
	global mpd_status_songid
	global mpd_status_playlistlength
	global update_flag	
	global mpd_client
	global oled_timeout_counter
	global oled_saving
	
	pressed_both = 0
	
	if oled_saving == 0:
	
		if channel == BTN_MENU:
			print('Play')
			mpd_client.play(0)
			
		if channel == BTN_LEFT:
			print('Previous')
			mpd_client.previous()
			
			if(GPIO.input(BTN_RIGHT) == 0):
				print('abu')
				oled_saving = 1
				pressed_both = 1

		if channel == BTN_RIGHT:
			print('Next')
			mpd_client.next()
			song_num = mpd_status_songid + 1
			
			if(GPIO.input(BTN_LEFT) == 0):
				print('abu')
				oled_saving = 1;
				pressed_both = 1
		
	update_flag = 1	
	if pressed_both == 0:
		oled_timeout_counter = OLED_TIMEOUT
		oled_saving = 0

def main():

	global song_num
	global mpd_status_songid
	global mpd_status_playlistlength
	global update_flag
	global mpd_client
	
	url_rds_opus = "http://www.lrt.lt/scripts/rdsOpus.php"
	url_rds_power_hit_radio = "http://powerhitradio.tv3.lt/hotnot/onair/nowjson"
	url_rds_tau = "http://www.tau.lt/info.dat"
	ulr_rds_bbc_one = "http://polling.bbc.co.uk/radio/realtime/bbc_radio_one.jsonp"
	ulr_rds_bbc_xtra = "http://polling.bbc.co.uk/radio/realtime/bbc_1xtra.jsonp"
	
	remove_str = 'Radio station '
	old_songid = 0
	
	loopas = 0
	
	#buttons
	GPIO.setmode(GPIO.BCM)
	GPIO.setup(BTN_LEFT, GPIO.IN, pull_up_down = GPIO.PUD_UP)
	GPIO.setup(BTN_MENU, GPIO.IN, pull_up_down = GPIO.PUD_UP)
	GPIO.setup(BTN_RIGHT, GPIO.IN, pull_up_down = GPIO.PUD_UP)
	GPIO.add_event_detect(BTN_LEFT, GPIO.FALLING, callback = my_callback)
	GPIO.add_event_detect(BTN_MENU, GPIO.FALLING, callback = my_callback)
	GPIO.add_event_detect(BTN_RIGHT, GPIO.FALLING, callback = my_callback)
	
	
	# Main program block
	print('Starting Internet radio')
 
	#GPIO.setmode(GPIO.BCM)			 # Use BCM GPIO numbers
	GPIO.setwarnings(False)
	
	GPIO.setup(LCD_E, GPIO.OUT)	# E
	GPIO.setup(LCD_RS, GPIO.OUT) # RS
	GPIO.setup(LCD_D4, GPIO.OUT) # DB4
	GPIO.setup(LCD_D5, GPIO.OUT) # DB5
	GPIO.setup(LCD_D6, GPIO.OUT) # DB6
	GPIO.setup(LCD_D7, GPIO.OUT) # DB7
	
	# Initialise display
	#lcd_init()
	oled_init()
 
	lcd_byte(LCD_LINE_1, LCD_CMD)
	lcd_string("   Internet radio   ")
		
	lcd_byte(LCD_LINE_2, LCD_CMD)
	lcd_string("     Made by DR     ")
	
	time.sleep(3)
	display_task()		
	
	#lcd_byte(LCD_LINE_1, LCD_CMD)
	#lcd_string("      Check         ")
		
	#lcd_byte(LCD_LINE_2, LCD_CMD)
	#lcd_string(" internet connection")
	
	#mpd_client = mpd.MPDClient()										# Init MPD mpd_client
	try:
		mpd_client.connect(MPD_SERVER_IP_HOST, MPD_SERVER_PORT)			# Connect to local MPD Server
		print('Connected')
	except:
		print('Not Connected')
		pass
	
	#for aaa in range (0, 10):
	while True:
	#while False:
		print('    --- loop: %d' %loopas)
		loopas += 1
		
		#gauti info dainu junginejimui mygtukais
		try:
			mpd_info = mpd_client.status()
			
			if 'songid' in mpd_info:
				mpd_status_songid = int(mpd_info['songid'])
			else:
				mpd_status_songid = -1

			if 'playlistlength' in mpd_info:
				mpd_status_playlistlength = int(mpd_info['playlistlength'])
			else:
				mpd_status_playlistlength = -1	
			
		except:
			pass
			
		try:
			mpd_info = mpd_client.currentsong()
			mpd_status = mpd_client.status()

			mpd_songid = ' #' + str(int(mpd_status['songid'])+1) + '/' + mpd_status['playlistlength']	
			
			if old_songid != int(mpd_status['songid']):
				update_flag = 1
				
			old_songid = int(mpd_status['songid'])
			
			if mpd_status['state'] == 'play': #jei groja

				#######stoties pavadinimo formavimas
				if 'name' in mpd_info:												
					currentsong_name = mpd_info['name']
				else:
					currentsong_name = "-"
					#jei nera pavadinimo, bandau imti linko pabaiga
					if 'file' in mpd_info: 
						spli = re.split('[/]', mpd_info['file'])
						currentsong_name = spli[len(spli)-1]
				
				if currentsong_name == 'bbc_radio_one':
					currentsong_name = 'BBC Radio 1'
					
				if currentsong_name == 'bbc_1xtra':
					currentsong_name = 'BBC Radio 1Xtra'
				
				#pasalina remove_str nuo pradzios
				if currentsong_name.startswith(remove_str):
					currentsong_name = currentsong_name[len(remove_str):]
					
				currentsong_name_show = currentsong_name

				#center			
				if len(currentsong_name_show) < LCD_WIDTH:
					if update_flag == 0:
						currentsong_name_show = ' ' * ((LCD_WIDTH - len(currentsong_name_show))/2) + currentsong_name_show
				
				#pridedu tarpu kad butu ilgis pagal lcd ploti
				currentsong_name_show = currentsong_name_show + ' ' * (LCD_WIDTH - len(currentsong_name_show))
					
				#parodau saraso eile
				if update_flag == 1:		
					currentsong_name_show = currentsong_name_show[:(LCD_WIDTH  - len(mpd_songid) )] + mpd_songid
				
				#######dainos pavadinimo formavimas		
				
				if 'title' in mpd_info:												# Check to see if "title" title exists in the dict
					songtitle = mpd_info['title']									# If it does set songtitle to the id3 title
				elif 'file' in mpd_info:											# If it doesn't have a title use the filename
					songtitle = mpd_info['file']									# Set songtitle to the filename
				else:
					songtitle = "-"
					
				#stotim, kurios neteikia info gaunu is http (web)
				
				#Opus3
				if currentsong_name == 'Opus3':
					print('Opus3')
					
					try:
						get_response = requests.get(url_rds_opus)
						spli = re.split('["]', get_response.content) #3 - Artist, 7 - Title, 15 - RDS info
						
						opus_artist = spli[3]
						opus_title = spli[7]
						opus_rds_info = spli[15]
						
	
						if (
								opus_rds_info != '' and #jei yra rds info, tada ziuriu ar bent vienas laukas sutampa su ja kazkiek
								
								( opus_artist != '' and opus_artist.upper() == opus_rds_info[:len(opus_artist)].upper() ) or  
								( opus_artist != '' and opus_artist[:len(opus_rds_info)].upper() == opus_rds_info.upper() )or 
								
								( opus_title != '' and opus_title.upper() == opus_rds_info[:len(opus_title)].upper() )or
								( opus_title != '' and opus_title[:len(opus_rds_info)].upper() == opus_rds_info.upper() )
							):
							print 'lygus'

							#TODO: apjungti
							if opus_artist == '' and opus_title != '':
								songtitle = opus_title
							elif opus_title == '' and opus_artist != '':
								songtitle = opus_artist
							elif opus_artist != '' and opus_title != '':
								songtitle = opus_artist + " - " + opus_title
							
						else:
							print 'nelygus'
							
							if opus_rds_info != '':
								songtitle =  opus_rds_info + " ~ "
							else:
								songtitle = ''
							
							#TODO: apjungti
							if opus_artist == '' and opus_title != '':
								songtitle = songtitle + opus_title
							elif opus_title == '' and opus_artist != '':
								songtitle = songtitle + opus_artist
							elif opus_artist != '' and opus_title != '':
								songtitle = songtitle + opus_artist + " - " + opus_title

					except:
						print('[Error RDS]')
						songtitle = '[Error RDS]'
						pass

				#Power Hit Radio
				if currentsong_name == 'Power Hit Radio':
					print('Power Hit Radio')

					try:
						get_response = requests.get(url_rds_power_hit_radio)
						spli = re.split('["]', get_response.content) #3 - Artist, 7 - Title
						songtitle = spli[3] + " - " + spli[7]
						
					except:
						print('[Error RDS]')
						songtitle = '[Error RDS]'
						pass
						
				#Radijas Tau
				if currentsong_name == 'Radijas TAU 102.9 FM':
					print('Radijas TAU 102.9 FM')

					try:
						get_response = requests.get(url_rds_tau)
						spli = get_response.content.splitlines() #0 - RDS, 1 - artist, 2 - title
						print spli
						songtitle = spli[0]
						
					except:
						print('[Error RDS]')
						songtitle = '[Error RDS]'
						pass
						
				#BBC Radio 1
				if currentsong_name == 'BBC Radio 1':
					print('BBC Radio 1')

					try:
						get_response = requests.get(ulr_rds_bbc_one)
						spli = re.split('["]', get_response.content) #17 - Artist, 21 - Title
						songtitle = spli[17] + " - " + spli[21]
						
					except:
						print('[Error RDS]')
						songtitle = '[Error RDS]'
						pass
						
				#BBC Radio 1Xtra
				if currentsong_name == 'BBC Radio 1Xtra':
					print('BBC Radio 1Xtra')

					try:
						get_response = requests.get(ulr_rds_bbc_xtra)
						spli = re.split('["]', get_response.content) #17 - Artist, 21 - Title
						songtitle = spli[17] + " - " + spli[21]
						
					except:
						print('[Error RDS]')
						songtitle = '[Error RDS]'
						pass
			else:
				currentsong_name = ''
				currentsong_name_show = currentsong_name
				
				print('[Not playing]')
				songtitle = '[Not playing]'
				
		except:
			currentsong_name = ''
			currentsong_name_show = currentsong_name
			print('[Error MPD]')
			songtitle = '[Error MPD]'
			
			try:
				mpd_client = mpd.MPDClient()
				#mpd_client.disconnect				
				mpd_client.connect(MPD_SERVER_IP_HOST, MPD_SERVER_PORT)						# Connect to local MPD Server
			except:
				print('[Error MPD con]')
				songtitle = '[Error MPD con]'
				pass
			pass

		songtitle_show = songtitle
			
		#center			
		if len(songtitle_show) < LCD_WIDTH:
			songtitle_show = ' ' * ((LCD_WIDTH - len(songtitle_show))/2) + songtitle_show
		
		update_flag = 0
		
		print(currentsong_name)
		print(songtitle)
		
		#mpd_client.disconnect()
		
		if (oled_saving == 1): #blank screen
			currentsong_name_show = " "
			songtitle_show = " "
			time.sleep(1)
		
		#isvedimas i LCD
		lcd_byte(LCD_LINE_1, LCD_CMD)
		lcd_string(currentsong_name_show)
			
		#rodyti teksta dalimis	
		for i in range (0, (((len(songtitle_show)-1)/LCD_WIDTH)+1) ): 
			lcd_byte(LCD_LINE_2, LCD_CMD)
			lcd_string(songtitle_show[(i*LCD_WIDTH):])
			if (update_flag == 0) and (oled_saving == 0):
				time.sleep(2.5)  # 2 second delay
				if i == 0:
					time.sleep(1) #papildomas uzlaikymas pimai daliai

def display_task():
	global oled_timeout_counter
	global oled_saving

	threading.Timer(1, display_task).start()
	
	if (oled_timeout_counter > 0):
		oled_timeout_counter = oled_timeout_counter - 1
	else:	
		oled_saving = 1
					
def lcd_init():
	print('lcd_init')

	# Initialise display
	lcd_byte(0x33,LCD_CMD)
	lcd_byte(0x32,LCD_CMD)
	lcd_byte(0x28,LCD_CMD)
	lcd_byte(0x0C,LCD_CMD)
	lcd_byte(0x06,LCD_CMD)
	lcd_byte(0x01,LCD_CMD) #clear display?
	
def oled_init():
	print('oled_init')
	
	# Initialise display into 4 bit mode
	lcd_byte(0x33,LCD_CMD)
	lcd_byte(0x32,LCD_CMD)
	
	# Now perform remainder of display init in 4 bit mode - IMPORTANT!
	# These steps MUST be exactly as follows, as OLEDs in particular are rather fussy	
	lcd_byte(0x28,LCD_CMD)# two lines and correct font DL = 0, N = 1 (NUMBER OF DISPLAY LINE: 2 -Line Display), F = 0 (CHARACTER FONT SET: 5 x 8 dots), FT1 = 0, FT0 = 0 (FONT TABLE SELECTION: ENGLISH_JAPANESE)
	lcd_byte(0x08,LCD_CMD)# display OFF, cursor/blink off
	lcd_byte(0x01,LCD_CMD) # clear display, waiting for longer delay
	lcd_byte(0x06,LCD_CMD)# entry mode set
	
	# extra steps required for OLED initialisation (no effect on LCD)
	lcd_byte(0x17,LCD_CMD)# character mode, power on
	
	# now turn on the display, ready for use - IMPORTANT!
	lcd_byte(0x0C,LCD_CMD)    # display on, cursor/blink off
	
def lcd_string(message):
	# Send string to display
 
	message = message.ljust(LCD_WIDTH," ") 
 
	for i in range(LCD_WIDTH):
		lcd_byte(ord(message[i]),LCD_CHR)
 
def lcd_byte(bits, mode):
	# Send byte to data pins
	# bits = data
	# mode = True	for character
	#				False for command
 
	GPIO.output(LCD_RS, mode) # RS
 
	# High bits
	GPIO.output(LCD_D4, False)
	GPIO.output(LCD_D5, False)
	GPIO.output(LCD_D6, False)
	GPIO.output(LCD_D7, False)
	if bits&0x10==0x10:
		GPIO.output(LCD_D4, True)
	if bits&0x20==0x20:
		GPIO.output(LCD_D5, True)
	if bits&0x40==0x40:
		GPIO.output(LCD_D6, True)
	if bits&0x80==0x80:
		GPIO.output(LCD_D7, True)
 
	# Toggle 'Enable' pin
	time.sleep(E_DELAY)
	GPIO.output(LCD_E, True)
	time.sleep(E_PULSE)
	GPIO.output(LCD_E, False)
	time.sleep(E_DELAY)		 
 
	# Low bits
	GPIO.output(LCD_D4, False)
	GPIO.output(LCD_D5, False)
	GPIO.output(LCD_D6, False)
	GPIO.output(LCD_D7, False)
	if bits&0x01==0x01:
		GPIO.output(LCD_D4, True)
	if bits&0x02==0x02:
		GPIO.output(LCD_D5, True)
	if bits&0x04==0x04:
		GPIO.output(LCD_D6, True)
	if bits&0x08==0x08:
		GPIO.output(LCD_D7, True)
 
	# Toggle 'Enable' pin
	time.sleep(E_DELAY)
	GPIO.output(LCD_E, True)
	time.sleep(E_PULSE)
	GPIO.output(LCD_E, False)
	time.sleep(E_DELAY)	
	
if __name__ == '__main__':
	main()
