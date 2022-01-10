# -*- coding: utf-8 -*-    
from functions import *
from src.logger import logger, loggerMapClicked
import time
import sys

def main():
    logger('Initializing Bombcrypto Bot...', sendTelegram=True)

    # Setup
    initConfig()

    last = {
    "login" : 0,
    "heroes" : 0,
    "new_map" : 0,
    "check_for_captcha" : 0,
    "refresh_heroes" : 0,
    "send_screenshot" : 0,
    "send_stashscreen" : 0
    }

    logger('Initialized. Status: Running', sendTelegram=True)
    while True:
        now = time.time()

        if now - last["heroes"] > addRandomness(configIntervals['send_heroes_for_work'] * 60):
            last["heroes"] = now
            refreshHeroes()

        if now - last["login"] > addRandomness(configIntervals['check_for_login'] * 60):
            sys.stdout.flush()
            last["login"] = now
            tryLogin()

        if now - last["new_map"] > configIntervals['check_for_new_map_button']:
            last["new_map"] = now
            tryClickNewMap()

        if now - last["refresh_heroes"] > addRandomness(configIntervals['refresh_heroes_positions'] * 60):
            last["refresh_heroes"] = now
            refreshHeroesPositions()

        if now - last["send_screenshot"] > addRandomness(config['telegram']['send_screenshot_interval'] * 60):
            last["send_screenshot"] = now
            sendScreenShotToTelegram()

        if now - last["send_stashscreen"] > addRandomness(config['telegram']['send_stashscreen_interval'] * 60):
            if sendStashScreenToTelegram():
                last["send_stashscreen"] = now

        #clickBtn(teasureHunt)
        logger(None, progress_indicator=True)

        sys.stdout.flush()

        time.sleep(1)



if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logger('⚠️ Execution error: %s' % str(e), sendTelegram=True)



#cv2.imshow('img',sct_img)
#cv2.waitKey()

# colocar o botao em pt
# soh resetar posiçoes se n tiver clickado em newmap em x segundos


