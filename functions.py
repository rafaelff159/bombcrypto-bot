# -*- coding: utf-8 -*-    
import threading
from src.logger import logger
from cv2 import cv2
from os import listdir
from random import randint
from random import random
import numpy as np
import mss
import pyautogui
import time
import sys
import yaml
from src.telegram_functions import telegram_bot_sendimage
import datetime
import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    ConversationHandler,
    CallbackContext,
)

#Init config variables
stream = open("config.yaml", 'r')
config = yaml.safe_load(stream)

configThreshold = config['threshold']

configHome = config['home']

configIntervals = config['time_intervals']

def initConfig():
    pyautogui.PAUSE = configIntervals['interval_between_moviments']

    global login_attempts
    login_attempts = 0

    global last_log_is_progress
    last_log_is_progress = False

    global images
    images = load_images()

def initBot():

    last = {
    "login" : 0,
    "heroes" : 0,
    "new_map" : 0,
    "check_for_captcha" : 0,
    "refresh_heroes" : 0,
    "send_screenshot" : 0,
    "send_stashscreen" : 0
    }

    t = threading.currentThread()
    while getattr(t, "running", True):
        now = time.time()

        if now - last["login"] > addRandomness(configIntervals['check_for_login'] * 60):
            sys.stdout.flush()
            last["login"] = now
            tryLogin()
        
        if not getattr(t, "running", True):
            break
        if now - last["heroes"] > addRandomness(configIntervals['send_heroes_for_work'] * 60):
            last["heroes"] = now
            refreshHeroes(config['select_heroes_mode'])

        if not getattr(t, "running", True):
            break
        if now - last["new_map"] > configIntervals['check_for_new_map_button']:
            last["new_map"] = now
            tryClickNewMap()

        if not getattr(t, "running", True):
            break
        if now - last["refresh_heroes"] > addRandomness(configIntervals['refresh_heroes_positions'] * 60):
            last["refresh_heroes"] = now
            refreshHeroesPositions()

        logger(None, progress_indicator=True)

        sys.stdout.flush()

        time.sleep(1)
    
    logger('Bombcrypto Bot Stopped', sendTelegram=True)

def addRandomness(n, randomn_factor_size=None):
    """Returns n with randomness
    Parameters:
        n (int): A decimal integer
        randomn_factor_size (int): The maximum value+- of randomness that will be
            added to n

    Returns:
        int: n with randomness
    """

    if randomn_factor_size is None:
        randomness_percentage = 0.1
        randomn_factor_size = randomness_percentage * n

    random_factor = 2 * random() * randomn_factor_size
    if random_factor > 5:
        random_factor = 5
    without_average_random_factor = n - randomn_factor_size
    randomized_n = int(without_average_random_factor + random_factor)
    # logger('{} with randomness -> {}'.format(int(n), randomized_n))
    return int(randomized_n)

def moveToWithRandomness(x,y,t):
    pyautogui.moveTo(addRandomness(x,10),addRandomness(y,10),t+random()/2)


def remove_suffix(input_string, suffix):
    """Returns the input_string without the suffix"""

    if suffix and input_string.endswith(suffix):
        return input_string[:-len(suffix)]
    return input_string

def load_images(dir_path='./targets/'):
    """ Programatically loads all images of dir_path as a key:value where the
        key is the file name without the .png suffix

    Returns:
        dict: dictionary containing the loaded images as key:value pairs.
    """

    file_names = listdir(dir_path)
    targets = {}
    for file in file_names:
        path = 'targets/' + file
        targets[remove_suffix(file, '.png')] = cv2.imread(path)

    return targets


def loadHeroesToSendHome():
    """Loads the images in the path and saves them as a list"""
    file_names = listdir('./targets/heroes-to-send-home')
    heroes = []
    for file in file_names:
        path = './targets/heroes-to-send-home/' + file
        heroes.append(cv2.imread(path))

    print('>>---> %d heroes that should be sent home loaded' % len(heroes))
    return heroes





def show(rectangles, img = None):
    """ Show an popup with rectangles showing the rectangles[(x, y, w, h),...]
        over img or a printSreen if no img provided. Useful for debugging"""

    if img is None:
        with mss.mss() as sct:
            monitor = sct.monitors[0]
            img = np.array(sct.grab(monitor))

    for (x, y, w, h) in rectangles:
        cv2.rectangle(img, (x, y), (x + w, y + h), (255,255,255,255), 2)

    # cv2.rectangle(img, (result[0], result[1]), (result[0] + result[2], result[1] + result[3]), (255,50,255), 2)
    cv2.imshow('img',img)
    cv2.waitKey(0)





def clickBtn(img, timeout=3, threshold = configThreshold['default']):
    """Search for img in the scree, if found moves the cursor over it and clicks.
    Parameters:
        img: The image that will be used as an template to find where to click.
        timeout (int): Time in seconds that it will keep looking for the img before returning with fail
        threshold(float): How confident the bot needs to be to click the buttons (values from 0 to 1)
    """

    logger(None, progress_indicator=True)
    start = time.time()
    has_timed_out = False
    while(not has_timed_out):
        matches = positions(img, threshold=threshold)

        if(len(matches)==0):
            has_timed_out = time.time()-start > timeout
            continue

        x,y,w,h = matches[0]
        pos_click_x = x+w/2
        pos_click_y = y+h/2
        moveToWithRandomness(pos_click_x,pos_click_y,1)
        pyautogui.click()
        return True

    return False

def printSreen():
    with mss.mss() as sct:
        monitor = sct.monitors[0]
        sct_img = np.array(sct.grab(monitor))
        # The screen part to capture
        # monitor = {"top": 160, "left": 160, "width": 1000, "height": 135}

        # Grab the data
        return sct_img[:,:,:3]

def positions(target, threshold=configThreshold['default'],img = None):
    if img is None:
        img = printSreen()
    result = cv2.matchTemplate(img,target,cv2.TM_CCOEFF_NORMED)
    w = target.shape[1]
    h = target.shape[0]

    yloc, xloc = np.where(result >= threshold)


    rectangles = []
    for (x, y) in zip(xloc, yloc):
        rectangles.append([int(x), int(y), int(w), int(h)])
        rectangles.append([int(x), int(y), int(w), int(h)])

    rectangles, weights = cv2.groupRectangles(rectangles, 1, 0.2)
    return rectangles

def scroll():
    dividers = positions(images['divider'], threshold = configThreshold['divider'])
    if (len(dividers) == 0):
        return
    x,y,w,h = dividers[len(dividers)-1]
#
    moveToWithRandomness(x,y,1)

    if not config['use_click_and_drag_instead_of_scroll']:
        pyautogui.scroll(-config['scroll_size'])
    else:
        pyautogui.dragRel(0,-config['click_and_drag_amount'],duration=1, button='left')


def clickWorkAll():
    clickBtn(images['work-all'])
    return 0

def sendRestAll():
    goToHeroes()
    clickBtn(images['rest-all'])
    goToGame()
    return 0

def isHome(hero, buttons):
    y = hero[1]

    for (_,button_y,_,button_h) in buttons:
        isBelow = y < (button_y + button_h)
        isAbove = y > (button_y - button_h)
        if isBelow and isAbove:
            # if send-home button exists, the hero is not home
            return False
    return True

def isWorking(bar, buttons):
    y = bar[1]

    for (_,button_y,_,button_h) in buttons:
        isBelow = y < (button_y + button_h)
        isAbove = y > (button_y - button_h)
        if isBelow and isAbove:
            return False
    return True

def clickGreenBarButtons():
    # ele clicka nos q tao trabaiano mas axo q n importa
    offset = 140

    green_bars = positions(images['green-bar'], threshold=configThreshold['green_bar'])
    logger('🟩 %d green bars detected' % len(green_bars))
    buttons = positions(images['go-work'], threshold=configThreshold['go_to_work_btn'])
    logger('🆗 %d buttons detected' % len(buttons))


    not_working_green_bars = []
    for bar in green_bars:
        if not isWorking(bar, buttons):
            not_working_green_bars.append(bar)
    if len(not_working_green_bars) > 0:
        logger('🆗 %d buttons with green bar detected' % len(not_working_green_bars))
        logger('👆 Clicking in %d heroes' % len(not_working_green_bars))

    # se tiver botao com y maior que bar y-10 e menor que y+10
    hero_clicks_cnt = 0
    for (x, y, w, h) in not_working_green_bars:
        # isWorking(y, buttons)
        moveToWithRandomness(x+offset+(w/2),y+(h/2),1)
        pyautogui.click()
        hero_clicks_cnt = hero_clicks_cnt + 1
        if hero_clicks_cnt > 20:
            logger('⚠️ Too many hero clicks, try to increase the go_to_work_btn threshold', sendTelegram=True)
            return
        #cv2.rectangle(sct_img, (x, y) , (x + w, y + h), (0,255,255),2)
    return len(not_working_green_bars)

def clickFullBarButtons():
    offset = 100
    full_bars = positions(images['full-stamina'], threshold=configThreshold['default'])
    buttons = positions(images['go-work'], threshold=configThreshold['go_to_work_btn'])

    not_working_full_bars = []
    for bar in full_bars:
        if not isWorking(bar, buttons):
            not_working_full_bars.append(bar)

    if len(not_working_full_bars) > 0:
        logger('👆 Clicking in %d heroes' % len(not_working_full_bars))

    for (x, y, w, h) in not_working_full_bars:
        moveToWithRandomness(x+offset+(w/2),y+(h/2),1)
        pyautogui.click()

    return len(not_working_full_bars)

def goToHeroes():
    if clickBtn(images['go-back-arrow']):
        global login_attempts
        login_attempts = 0

    #TODO tirar o sleep quando colocar o pulling
    time.sleep(1)
    clickBtn(images['hero-icon'])
    time.sleep(randint(1,3))

def goToGame():
    # in case of server overload popup
    clickBtn(images['x'])
    # time.sleep(3)
    clickBtn(images['x'])

    clickBtn(images['treasure-hunt-icon'])

def refreshHeroesPositions():
    logger('🔃 Refreshing Heroes Positions')
    clickBtn(images['go-back-arrow'])
    clickBtn(images['treasure-hunt-icon'])
    time.sleep(1)
    clickBtn(images['treasure-hunt-icon'])

def tryLogin():
    global login_attempts
    logger('😿 Checking if game has disconnected')

    if login_attempts > 3:
        logger('🔃 Too many login attempts, refreshing')
        login_attempts = 0
        pyautogui.hotkey('ctrl','f5')
        return

    if clickBtn(images['ok']):
        time.sleep(1)
        pass

    if clickBtn(images['connect-wallet'], threshold = configThreshold['select_wallet_buttons']):
        logger('🎉 Connect wallet button detected, logging in!', sendTelegram=True)
        login_attempts = login_attempts + 1
        #TODO mto ele da erro e poco o botao n abre
        time.sleep(10)

    if clickBtn(images['select-wallet-2'], threshold = configThreshold['select_wallet_buttons']):
        # sometimes the sign popup appears imediately
        login_attempts = login_attempts + 1
        time.sleep(20)
        # print('{} login attempt'.format(login_attempts))
        if clickBtn(images['treasure-hunt-icon'], timeout = 15):
            logger('🆗 Sucessfully login, treasure hunt btn clicked', sendTelegram=True)
            login_attempts = 0
        return
        # click ok button

    if not clickBtn(images['select-wallet-1-no-hover'], threshold = configThreshold['select_wallet_buttons']):
        if clickBtn(images['select-wallet-1-hover'], threshold = configThreshold['select_wallet_buttons']):
            pass
            # o ideal era que ele alternasse entre checar cada um dos 2 por um tempo 
            # print('sleep in case there is no metamask text removed')
            # time.sleep(20)
    else:
        pass
        # print('sleep in case there is no metamask text removed')
        # time.sleep(20)

    if clickBtn(images['select-wallet-2'], threshold = configThreshold['select_wallet_buttons']):
        login_attempts = login_attempts + 1
        # print('sign button clicked')
        # print('{} login attempt'.format(login_attempts))
        time.sleep(20)
        if clickBtn(images['treasure-hunt-icon'], threshold = configThreshold['select_wallet_buttons']):
            logger('🆗 Sucessfully login, treasure hunt btn clicked', sendTelegram=True)
            login_attempts = 0
        # time.sleep(15)

    if clickBtn(images['ok']):
        pass
        # time.sleep(15)
        # print('ok button clicked')
    
    if login_attempts > 0:
        logger('⚠️ Unsuccessful login attempt. Attempt: %d' % login_attempts, sendTelegram=True)



def sendHeroesHome():
    if not configHome['enable']:
        return
        
    home_heroes = loadHeroesToSendHome()
    goToHeroes()
    empty_scrolls_attempts = config['scroll_attemps']
    while(empty_scrolls_attempts >0):
        heroes_positions = []
        for hero in home_heroes:
            hero_positions = positions(hero, threshold=configHome['hero_threshold'])
            if not len (hero_positions) == 0:
                #TODO maybe pick up match with most wheight instead of first
                hero_position = hero_positions[0]
                heroes_positions.append(hero_position)

        n = len(heroes_positions)
        if n == 0:
            print('No heroes that should be sent home found.')
            return
        print(' %d heroes that should be sent home found' % n)
        # if send-home button exists, the hero is not home
        go_home_buttons = positions(images['send-home'], threshold=configHome['home_button_threshold'])
        # TODO pass it as an argument for both this and the other function that uses it
        go_work_buttons = positions(images['go-work'], threshold=configThreshold['go_to_work_btn'])

        for position in heroes_positions:
            if not isHome(position,go_home_buttons):
                print(isWorking(position, go_work_buttons))
                if(not isWorking(position, go_work_buttons)):
                    print ('hero not working, sending him home')
                    moveToWithRandomness(go_home_buttons[0][0]+go_home_buttons[0][2]/2,position[1]+position[3]/2,1)
                    pyautogui.click()
                else:
                    print ('hero working, not sending him home(no dark work button)')
            else:
                print('hero already home, or home full(no dark home button)')

        empty_scrolls_attempts -= 1
        if empty_scrolls_attempts > 0:
            scroll()
        time.sleep(1)
    goToGame()





def refreshHeroes(mode):
    if mode == 'full':
        logger('⚒️ Sending heroes with full stamina bar to work', sendTelegram=True)
    elif mode == 'green':
        logger('⚒️ Sending heroes with green stamina bar to work', sendTelegram=True)
    else:
        logger('⚒️ Sending all heroes to work', sendTelegram=True)

    goToHeroes()

    if mode == 'all':
        clickWorkAll()
        logger('💪 All heroes sent to working', sendTelegram=True)
    else:
        buttonsClicked = 0
        hero_working = 0
        hero_clicked = 0
        empty_scrolls_attempts = config['scroll_attemps']

        while(empty_scrolls_attempts >0):
            hero_working += len(positions(images['working'], threshold=configThreshold['go_to_work_btn']))
            if mode == 'full':
                buttonsClicked = clickFullBarButtons()
            elif mode == 'green':
                buttonsClicked = clickGreenBarButtons()

            hero_clicked += buttonsClicked

            empty_scrolls_attempts -= 1

            if empty_scrolls_attempts > 0:
                scroll()
            
            time.sleep(2)
        if hero_clicked > 0:
            logger('💪 %d heroes sent to work (%d working now)' % (hero_clicked, (hero_working + hero_clicked)), sendTelegram=True)
        else:
            logger('💪 %d heroes are working' % hero_working, sendTelegram=True)

    goToGame()

def tryClickNewMap():
    if clickBtn(images['new-map']):
        time.sleep(1)
        sendStashScreenToTelegram()
        logger('🗺️ New Map button clicked!', sendTelegram=True)

def sendScreenShotToTelegram():
    q = datetime.datetime.now()
    d = q.strftime("%d%m%Y%H%M")
    image_file = os.path.join('targets', d +'.png')
    pyautogui.screenshot(image_file)
    telegram_bot_sendimage(image_file)
    os.remove(image_file)

def sendStashScreenToTelegram():
    if clickBtn(images['stash']):
        time.sleep(3)
        q = datetime.datetime.now()
        d = q.strftime("%d%m%Y%H%M")
        image_file = os.path.join('targets', d +'.png')
        pyautogui.screenshot(image_file)
        telegram_bot_sendimage(image_file)
        os.remove(image_file)
        clickBtn(images['x'])

def sendHeroesScreenToTelegram():
    goToHeroes()
    empty_scrolls_attempts = config['scroll_attemps']
    while(empty_scrolls_attempts >0):
        sendScreenShotToTelegram()
        empty_scrolls_attempts -= 1
        if empty_scrolls_attempts > 0:
            scroll()
        time.sleep(1)
    goToGame()


#Telegram functions ---------------------------------------

bot_enabled = config['telegram']['enabled']
bot_token = config['telegram']['token_api']
bot_chatID = config['telegram']['chat_id']

botThread: threading.Thread
STARTED = range(1)
reply_keyboard_commands = [['/start', '/stop', '/restall'], ['/workall', '/workfull', '/workgreen'], ['/printscreen', '/printstash', '/printheroes']]

def startTelegram(update: Update, context: CallbackContext) -> int:
    if bot_enabled and str(update.message.chat_id) == bot_chatID:
        update.message.reply_text('Initialiting Bombcrypto Bot', reply_markup=ReplyKeyboardMarkup(
            reply_keyboard_commands,
            resize_keyboard=True,
            input_field_placeholder='Available commands'
        ))
        global botThread
        botThread = threading.Thread(target=initBot)
        botThread.start()
        return STARTED

def stopTelegram(update: Update, context: CallbackContext) -> int:
    if bot_enabled and str(update.message.chat_id) == bot_chatID:
        update.message.reply_text('Sending interrupting signal...')
        botThread.running = False
        return ConversationHandler.END

def printscreenTelegram(update: Update, context: CallbackContext) -> int:
    if bot_enabled and str(update.message.chat_id) == bot_chatID:
        sendScreenShotToTelegram()
        return STARTED

def printstashTelegram(update: Update, context: CallbackContext) -> int:
    if bot_enabled and str(update.message.chat_id) == bot_chatID:
        sendStashScreenToTelegram()
        return STARTED

def printheroesTelegram(update: Update, context: CallbackContext) -> int:
    if bot_enabled and str(update.message.chat_id) == bot_chatID:
        sendHeroesScreenToTelegram()
        return STARTED

def workallTelegram(update: Update, context: CallbackContext) -> int:
    if bot_enabled and str(update.message.chat_id) == bot_chatID:
        refreshHeroes('all')
        return STARTED

def workfullTelegram(update: Update, context: CallbackContext) -> int:
    if bot_enabled and str(update.message.chat_id) == bot_chatID:
        refreshHeroes('full')
        return STARTED

def workgreenTelegram(update: Update, context: CallbackContext) -> int:
    if bot_enabled and str(update.message.chat_id) == bot_chatID:
        refreshHeroes('green')
        return STARTED

def restallTelegram(update: Update, context: CallbackContext) -> int:
    if bot_enabled and str(update.message.chat_id) == bot_chatID:
        update.message.reply_text('Sending heroes to rest...')
        sendRestAll()
        update.message.reply_text('All heroes sent to rest')
        return STARTED

def initTelegram() -> None:
    if bot_enabled:
        updater = Updater(bot_token)
        dispatcher = updater.dispatcher

        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', startTelegram)],
            states={
                STARTED: [
                    CommandHandler('stop', stopTelegram),
                    CommandHandler('printscreen', printscreenTelegram),
                    CommandHandler('printstash', printstashTelegram),
                    CommandHandler('printheroes', printheroesTelegram),
                    CommandHandler('workall', workallTelegram),
                    CommandHandler('workfull', workfullTelegram),
                    CommandHandler('workgreen', workgreenTelegram),
                    CommandHandler('restall', restallTelegram)
                ]
            },
            fallbacks=[CommandHandler('stop', stopTelegram)],
        )
        dispatcher.add_handler(conv_handler)

        updater.start_polling()
        updater.idle()


