from os import path as ospath, mkdir, system, getenv
from logging import INFO, ERROR, FileHandler, StreamHandler, basicConfig, getLogger
from traceback import format_exc
from asyncio import Queue, Lock

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pyrogram import Client
from pyrogram.enums import ParseMode
from dotenv import load_dotenv
from uvloop import install

install()
basicConfig(format="[%(asctime)s] [%(name)s | %(levelname)s] - %(message)s [%(filename)s:%(lineno)d]",
            datefmt="%m/%d/%Y, %H:%M:%S %p",
            handlers=[FileHandler('log.txt'), StreamHandler()],
            level=INFO)

getLogger("pyrogram").setLevel(ERROR)
LOGS = getLogger(__name__)

load_dotenv('config.env')

ani_cache = {
    'fetch_animes': True,
    'ongoing': set(),
    'completed': set()
}
ffpids_cache = list()

ffLock = Lock()
ffQueue = Queue()
ff_queued = dict()

class Var:
    API_ID, API_HASH, BOT_TOKEN = getenv("API_ID"), getenv("API_HASH"), getenv("BOT_TOKEN")
    MONGO_URI = getenv("MONGO_URI")
    
    if not BOT_TOKEN or not API_HASH or not API_ID or not MONGO_URI:
        LOGS.critical('Important Variables Missing. Fill Up and Retry..!! Exiting Now...')
        exit(1)

    RSS_ITEMS = getenv("RSS_ITEMS", "https://subsplease.org/rss/?r=1080").split()
    POST_STICKERS = [
    "CAACAgUAAxkBAAEOPE5n8LiWD6pel6oUzN5OXPZ2xcaiPwACiRoAAtmqiFcd7x7ZUW-tRTYE",
    "CAACAgUAAxkBAAEOPFBn8LiZ7EXXTi_mVEVmn9vHRivTJgACrxEAAuNtgFfdHSWM1CIl6DYE",
    "CAACAgUAAxkBAAEOPFFn8LiaQzJPB6t93beNpQE9Xnp4ugACkhkAArPagFeh_Fw7Nr9ipjYE",
    "CAACAgUAAxkBAAEOPFJn8LiaNZqqIhogXx9IT_Kc6b2LZgAC_BQAAmUsgFdp7eH7MDAAAac2BA",
    "CAACAgIAAxkBAAEOPFZn8L7LzEV8_mu-FHFTJyhCSTpVdwACjUsAAlpAwEsgcRoyBIm3LTYE",
    "CAACAgIAAxkBAAEOPFdn8L7Lq9PHhTEuvgoGVfzCwdtGlgACqQ4AAtsUkUlf3jwyEK2NVzYE",
    "CAACAgEAAxkBAAEOPFhn8L7L6U00H66JeZJnau9kKpOYpwACcwIAAuZKaUZppiI4LNKJPzYE",
    "CAACAgUAAxkBAAEOPFln8L7L1e3u8iecsRxVUSOwQfsRZgACyBIAAsGkwVST6GCxYt6DZTYE",
    "CAACAgUAAxkBAAEOPFpn8L7LbaQaD9GYk79CPOym3-FtBQACZRIAAkrdMFZ_l8NyREcnPDYE",
    "CAACAgIAAxkBAAEOPFtn8L7Lx0u-ZSEK3Xy2zQ_DNJ5UPwACMxMAAuQ-KUiTFPeKnXEo5DYE",
    "CAACAgUAAxkBAAEOPFxn8L7L56liwZuV1IpwBys00N8-KgACcQsAAlgFmFcGLC3m_JBZTzYE",
    "CAACAgIAAxkBAAEOPF1n8L7LbFHt2jxb3IUS9SWMuUoBVQACFF8AAuldWUjnSy6fL0VazjYE",
    "CAACAgQAAxkBAAEOPF5n8L7LHDFwMYRVGqsgXoF805peNAADGQACVLQxUD6v__V2kulmNgQ",
    "CAACAgEAAxkBAAEOPF9n8L7Lh24ipPSkFzQD2O5eJ5h3qAACfAIAAmBPyUfynB_fIm1i_jYE",
    "CAACAgUAAxkBAAEOPGBn8L7L1gnVw0h86ZyQfo3Du4nJGAACYAgAAuzyGVaXrWVIzlmcXjYE",
    "CAACAgQAAxkBAAEOPGFn8L7LASXOtdfJSCfcQ50U0eNsIQAC5BEAAuOS-VDx5MutTFPnKzYE",
    "CAACAgQAAxkBAAEOPGJn8L7LjMXnzUpFSVHr3rmETDxqqAACDwsAAlmRcVLDm1A3FsLyjTYE",
    "CAACAgUAAxkBAAEOPGNn8L7LDrqgTeU1aFndPiZHuJsiLQACWwUAAjz_KVQ2DB1FN_nBKDYE"
]
    FSUB_CHATS = list(map(int, getenv('FSUB_CHATS').split()))
    BACKUP_CHANNEL = getenv("BACKUP_CHANNEL") or ""
    MAIN_CHANNEL = int(getenv("MAIN_CHANNEL"))
    LOG_CHANNEL = int(getenv("LOG_CHANNEL") or 0)
    FILE_STORE = int(getenv("FILE_STORE"))
    ADMINS = list(map(int, getenv("ADMINS", "1242011540").split()))
    
    SEND_SCHEDULE = getenv("SEND_SCHEDULE", "False").lower() == "true"
    BRAND_UNAME = getenv("BRAND_UNAME", "@username")
    FFCODE_1080 = getenv("FFCODE_1080") or """ffmpeg -i '{}' -progress '{}' -preset veryfast -c:v libx264 -s 1920x1080 -pix_fmt yuv420p -crf 30 -c:a libopus -b:a 32k -c:s copy -map 0 -ac 2 -ab 32k -vbr 2 -level 3.1 '{}' -y"""
    FFCODE_720 = getenv("FFCODE_720") or """ffmpeg -i '{}' -progress '{}' -preset superfast -c:v libx264 -s 1280x720 -pix_fmt yuv420p -crf 30 -c:a libopus -b:a 32k -c:s copy -map 0 -ac 2 -ab 32k -vbr 2 -level 3.1 '{}' -y"""
    FFCODE_480 = getenv("FFCODE_480") or """ffmpeg -i '{}' -progress '{}' -preset superfast -c:v libx264 -s 854x480 -pix_fmt yuv420p -crf 30 -c:a libopus -b:a 32k -c:s copy -map 0 -ac 2 -ab 32k -vbr 2 -level 3.1 '{}' -y"""
    FFCODE_Hdrip = getenv("FFCODE_Hdrip") or """ffmpeg -i '{}' -progress '{}' -preset superfast -c:v libx264 -s 640x360 -pix_fmt yuv420p -crf 30 -c:a libopus -b:a 32k -c:s copy -map 0 -ac 2 -ab 32k -vbr 2 -level 3.1 '{}' -y"""
    QUALS = getenv("QUALS", "Hdrip 480 720 1080").split()
    
    AS_DOC = getenv("AS_DOC", "True").lower() == "true"
    THUMB = getenv("THUMB", "https://te.legra.ph/file/621c8d40f9788a1db7753.jpg")
    AUTO_DEL = getenv("AUTO_DEL", "True").lower() == "true"
    DEL_TIMER = int(getenv("DEL_TIMER", "600"))
    START_PHOTO = getenv("START_PHOTO", "https://te.legra.ph/file/120de4dbad87fb20ab862.jpg")
    START_MSG = getenv("START_MSG", "<b>Hey {first_name}</b>,\n\n    <i>I am Auto Animes Store & Automater Encoder Build with â¤ï¸ !!</i>")
    START_BUTTONS = getenv("START_BUTTONS", "TeamWarlords|https://Telegram.dog/TeamWarlords Ongoing|https://Telegram.dog/Daily_Animes_Piras")

if Var.THUMB and not ospath.exists("thumb.jpg"):
    system(f"wget -q {Var.THUMB} -O thumb.jpg")
    LOGS.info("Thumbnail has been Saved!!")
if not ospath.isdir("encode/"):
    mkdir("encode/")
if not ospath.isdir("thumbs/"):
    mkdir("thumbs/")
if not ospath.isdir("downloads/"):
    mkdir("downloads/")

try:
    bot = Client(name="AutoAniAdvance", api_id=Var.API_ID, api_hash=Var.API_HASH, bot_token=Var.BOT_TOKEN, plugins=dict(root="bot/modules"), parse_mode=ParseMode.HTML)
    bot_loop = bot.loop
    sch = AsyncIOScheduler(timezone="Asia/Kolkata", event_loop=bot_loop)
except Exception as ee:
    LOGS.error(str(ee))
    exit(1)
