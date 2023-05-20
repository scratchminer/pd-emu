import pygame as pg

from calendar import timegm
from datetime import datetime, timezone

from os import name as PLATFORM, system
from time import gmtime, localtime, sleep, time as epoch_sec
from threading import Thread

from loaders.pft import PFT_PALETTE
from pdemu import EMULATOR
from .runtime import RUNTIME

def pd_accelerometerIsRunning():
	return EMULATOR.accel.running

def pd_apiVersion():
	return 11370, 11300

def pd_buttonIsPressed(button):
	return EMULATOR.buttons[EMULATOR.get_button_constant(button)]

def pd_buttonJustPressed(button):
	return EMULATOR.buttons[EMULATOR.get_button_constant(button)] and \
		EMULATOR.buttons[EMULATOR.get_button_constant(button)] != EMULATOR.prev_buttons[EMULATOR.get_button_constant(button)]

def pd_buttonJustReleased(button):
	return EMULATOR.prev_buttons[EMULATOR.get_button_constant(button)] and \
		EMULATOR.buttons[EMULATOR.get_button_constant(button)] != EMULATOR.prev_buttons[EMULATOR.get_button_constant(button)]

def pd_clearConsole():
	system("cls" if PLATFORM == "nt" else "clear")

def pd_drawFPS(x, y):
	fps = str(round(EMULATOR.clock.get_fps()))
	fps_text = EMULATOR.fps_font.to_surf(fps)
	fps_surf = pg.Surface((fps_text.get_width() + 1, fps_text.get_height() + 2))
	fps_surf.fill(PFT_PALETTE[3])
	fps_surf.blit(fps_text, (0, 1))
	EMULATOR.display.blit(fps_surf, (x, y))

def pd_epochFromGMTTime(time):
	dt = datetime(time.year, time.month, time.day, time.hour, time.minute, time.second, time.millisecond * 1000, timezone.utc)
	epoch = (dt - datetime(2000, 1, 1, tzinfo=timezone.utc)).total_seconds()
	return int(epoch), round((epoch - int(epoch)) * 1000)

def pd_epochFromTime(time):
	dt = datetime(time.year, time.month, time.day, time.hour, time.minute, time.second, time.millisecond * 1000).astimezone(tz=None)
	epoch = (dt - datetime(2000, 1, 1, tzinfo=timezone.utc)).total_seconds()
	return int(epoch), round((epoch - int(epoch)) * 1000)

def pd_getBatteryPercentage():
	return EMULATOR.battery.pct

def pd_getBatteryVoltage():
	return EMULATOR.battery.voltage

def pd_getButtonState():
	current = 0
	pressed = 0
	released = 0
	
	for btn in range(6):
		if pd_buttonIsPressed(1 << btn): current |= (1 << btn)
		if pd_buttonJustPressed(1 << btn): pressed |= (1 << btn)
		if pd_buttonJustReleased(1 << btn): released |= (1 << btn)
	
	return current, pressed, released

def pd_getCrankChange():
	change = EMULATOR.crank.delta
	accelerated_change = change * EMULATOR.calculate_crank_velocity()
	return change, accelerated_change

def pd_getCrankPosition():
	return EMULATOR.crank.pos

def pd_getCurrentTimeMilliseconds():
	return EMULATOR.game_time

def pd_getElapsedTime():
	return epoch_sec() - EMULATOR.hires_time

def pd_getFlipped():
	return EMULATOR.settings.upside_down

def pd_getGMTTime():
	dt = datetime.now(tz=timezone.utc)
	time = dt.timetuple()
	return RUNTIME.table_from({
		"year": time.tm_year,
		"month": time.tm_month,
		"day": time.tm_mday,
		"weekday": time.tm_wday,
		"hour": time.tm_hour,
		"minute": time.tm_min,
		"second": time.tm_sec,
		"millisecond": round(dt.microsecond / 1000)
	})

def pd_getPowerStatus():
	return RUNTIME.table_from({
		"charging": EMULATOR.battery.charging
		"USB": EMULATOR.serial.enabled
	})

def pd_getReduceFlashing():
	return EMULATOR.settings.reduce_flashing

def pd_getSecondsSinceEpoch():
	dt = datetime.now(tz=timezone.utc)
	epoch = (dt - datetime(2000, 1, 1, tzinfo=timezone.utc)).total_seconds()
	return int(epoch), round((epoch - int(epoch)) * 1000)

# TODO: rework the garbage collector to be more like that of the device
def pd_getStats():
	return RUNTIME.table_from({
		"GC": EMULATOR.stats.gc_time / EMULATOR.stats.interval
		"game": EMULATOR.stats.game_time / EMULATOR.stats.interval
		"audio": EMULATOR.stats.audio_time / EMULATOR.stats.interval
		"idle": (EMULATOR.clock.get_time() - EMULATOR.clock.get_rawtime()) / (EMULATOR.stats.interval * 1000)
	})

def pd_getSystemLanguage():
	return EMULATOR.settings.language

def pd_getSystemMenu():
	return RUNTIME.table_from(EMULATOR.system_menu.formatted_dict)

def pd_getTime():
	dt = datetime.now(tz=timezone.utc).astimezone(tz=None)
	time = dt.timetuple()
	return RUNTIME.table_from({
		"year": time.tm_year,
		"month": time.tm_month,
		"day": time.tm_mday,
		"weekday": time.tm_wday,
		"hour": time.tm_hour,
		"minute": time.tm_min,
		"second": time.tm_sec,
		"millisecond": round(dt.microsecond / 1000)
	})

def pd_GMTTimeFromEpoch(seconds, milliseconds):
	epoch = int(seconds) + (int(milliseconds) / 1000)
	time = datetime(2000, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=epoch)
	return RUNTIME.table_from({
		"year": time.tm_year,
		"month": time.tm_month,
		"day": time.tm_mday,
		"weekday": time.tm_wday,
		"hour": time.tm_hour,
		"minute": time.tm_min,
		"second": time.tm_sec,
		"millisecond": round((epoch - int(epoch)) * 1000)
	})

def pd_isCrankDocked():
	return EMULATOR.crank.docked

def pd_readAccelerometer():
	return EMULATOR.accel.x, EMULATOR.accel.y, EMULATOR.accel.z

# def pd_reboot():

def pd_resetElapsedTime():
	EMULATOR.hires_time = epoch_sec()

def pd_setAutoLockDisabled(disable):
	EMULATOR.settings.auto_lock = not bool(disable)
	if not disable: EMULATOR.settings.auto_lock_timer = 60.0

def pd_setCollectsGarbage(flag):
	EMULATOR.gc.enabled = bool(flag)

def pd_setCrankSoundsDisabled(disable):
	EMULATOR.settings.crank_sounds = not bool(disable)

def pd_setGCScaling(min, max):
	EMULATOR.gc.min_mem = float(min)
	EMULATOR.gc.max_mem = float(max)

def pd_setMenuImage(image, xOffset=0):
	EMULATOR.system_menu.game_img = image.pdImg
	EMULATOR.system_menu.game_img_offset = int(xOffset)

def pd_setMinimumGCTime(ms):
	EMULATOR.gc.min_time = int(ms)

def pd_setNewlinePrinted(flag=True):
	EMULATOR.newline = "\n" if flag else ""

def pd_setStatsInterval(seconds):
	if float(seconds) == 0.0: EMULATOR.stats.enabled = False
	else:
		EMULATOR.stats.enabled = True
		EMULATOR.stats.interval = float(seconds)

def pd_start():
	with EMULATOR.call_update_lock: EMULATOR.call_update = True

def pd_startAccelerometer():
	EMULATOR.accel.running = True

def pd_stop():
	with EMULATOR.call_update_lock: EMULATOR.call_update = False

def pd_stopAccelerometer():
	EMULATOR.accel.running = False

def pd_timeFromEpoch(seconds, milliseconds):
	epoch = int(seconds) + int(milliseconds / 1000)
	time = datetime(2000, 1, 1).astimezone(tz=None) + timedelta(seconds=epoch)
	return RUNTIME.table_from({
		"year": time.tm_year,
		"month": time.tm_month,
		"day": time.tm_mday,
		"weekday": time.tm_wday,
		"hour": time.tm_hour,
		"minute": time.tm_min,
		"second": time.tm_sec,
		"millisecond": round((epoch - int(epoch)) * 1000)
	})

def pd_wait_cb(millis):
	pd_stop()
	sleep(millis / 1000)
	pd_start()

def pd_wait(millis):
	Thread(target=pd_wait_cb, name="playdate.wait()", args=(millis,), daemon=True)

PLAYDATE_API = {
	"accelerometerIsRunning": pd_accelerometerIsRunning,
	"apiVersion": pd_apiVersion,
	"buttonIsPressed": pd_buttonIsPressed,
	"buttonJustPressed": pd_buttonJustPressed,
	"buttonJustReleased": pd_buttonJustReleased,
	"clearConsole": pd_clearConsole,
	"drawFPS": pd_drawFPS,
	"epochFromGMTTime": pd_epochFromGMTTime,
	"epochFromTime": pd_epochFromTime,
	"getBatteryPercentage": pd_getBatteryPercentage,
	"getBatteryVoltage": pd_getBatteryVoltage,
	"getButtonState": pd_getButtonState,
	"getCrankChange": pd_getCrankChange,
	"getCrankPosition": pd_getCrankPosition,
	"getCurrentTimeMilliseconds": pd_getCurrentTimeMilliseconds,
	"getElapsedTime": pd_getElapsedTime,
	"getFlipped": pd_getFlipped,
	"getGMTTime": pd_getGMTTime,
	"getPowerStatus": pd_getPowerStatus,
	"getReduceFlashing": pd_getReduceFlashing,
	"getSecondsSinceEpoch": pd_getSecondsSinceEpoch,
	"getStats": pd_getStats,
	"getSystemLanguage": pd_getSystemLanguage,
	"getSystemMenu": pd_getSystemMenu,
	"getTime": pd_getTime,
	"GMTTimeFromEpoch": pd_GMTTimeFromEpoch,
	"isCrankDocked": pd_isCrankDocked,
	"readAccelerometer": pd_readAccelerometer,
	# "reboot": pd_reboot,
	"resetElapsedTime": pd_resetElapsedTime,
	"setAutoLockDisabled": pd_setAutoLockDisabled,
	"setCollectsGarbage": pd_setCollectsGarbage,
	"setCrankSoundsDisabled": pd_setCrankSoundsDisabled,
	"setGCScaling": pd_setGCScaling,
	"setMenuImage": pd_setMenuImage,
	"setMinimumGCTime": pd_setMinimumGCTime,
	"setNewlinePrinted": pd_setNewlinePrinted,
	"setStatsInterval": pd_setStatsInterval,
	"start": pd_start,
	"startAccelerometer": pd_startAccelerometer,
	"stop": pd_stop,
	"stopAccelerometer": pd_stopAccelerometer,
	"timeFromEpoch": pd_timeFromEpoch,
	"wait": pd_wait	
}