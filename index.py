# -*- coding: utf-8 -*-    
from functions import *
from src.logger import logger

def main():
    try:
        logger('Initializing Application', sendTelegram=True)
        # Setup
        initConfig()

        if config['telegram']['enabled']:
            initTelegram()
        else:
            logger('Initializing Bombcrypto Bot', sendTelegram=True)
            initBot()
    except Exception as e:
        logger('⚠️ Execution error: %s' % str(e), sendTelegram=True)
    finally:
        logger('Shutting down Application', sendTelegram=True)


if __name__ == '__main__':
    main()
