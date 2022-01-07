import os, platform
import subprocess
import json

from telegram import InlineKeyboardMarkup, Update

from time import sleep
from datetime import datetime
from typing import List

class TelegramHelper():
    def __init__(self, datafolder, config, configfile) -> None:
        self.datafolder = datafolder
        self.data = {}
        self.config = config
        self.config_file = configfile
        self.settings = {}
        self.use_default_scanner = 1
        self.atr72pcnt = 2.0
        self.enableleverage = False
        self.use_default_scanner = 1
        self.maxbotcount = 0
        self.autoscandelay = 0
        self.enable_buy_next = True
        self.autostart = False

        self.loadConfig()

    def loadConfig(self):
        self.read_config()

        if "scanner" in self.config:

            self.atr72pcnt = (
                self.config["scanner"]["atr72_pcnt"]
                if "atr72_pcnt" in self.config["scanner"]
                else self.atr72pcnt
            )
            self.enableleverage = (
                self.config["scanner"]["enableleverage"]
                if "enableleverage" in self.config["scanner"]
                else self.enableleverage
            )
            self.use_default_scanner = (
                self.config["scanner"]["use_default_scanner"]
                if "use_default_scanner" in self.config["scanner"]
                else self.use_default_scanner
            )
            self.maxbotcount = (
                self.config["scanner"]["maxbotcount"]
                if "maxbotcount" in self.config["scanner"]
                else self.maxbotcount
            )
            self.autoscandelay = (
                self.config["scanner"]["autoscandelay"]
                if "autoscandelay" in self.config["scanner"]
                else 0
            )
            self.enable_buy_next = (
                self.config["scanner"]["enable_buy_next"]
                if "enable_buy_next" in self.config["scanner"]
                else True
            )

    def sendtelegramMsg(self, update: Update, reply, markup: InlineKeyboardMarkup = None):
        try:
            update.callback_query.data = datetime.now().isoformat()
            query = update.callback_query
            query.answer()
        except:
            pass
        try:
            if markup == None:
                query.edit_message_text(reply, parse_mode="HTML")
            else:
                query.edit_message_text(reply, reply_markup=markup, parse_mode="HTML")
        except Exception as err:
            try:
                update.message.reply_text(reply, reply_markup=markup, parse_mode="HTML")
            except Exception as err:
                update.effective_message.reply_html(reply)
    def read_data(self, name: str = "data.json") -> bool:
        try:
            fname = name if name.__contains__(".json") else f"{name}.json"
            with open(
                os.path.join(self.datafolder, "telegram_data", fname), "r", encoding="utf8"
            ) as json_file:
                self.data = json.load(json_file)
        except FileNotFoundError:
            return False
        except json.decoder.JSONDecodeError:
            return False

        return True

    def write_data(self, name: str = "data.json") -> None:
        fname = name if name.__contains__(".json") else f"{name}.json"
        try:
            with open(
                os.path.join(self.datafolder, "telegram_data", fname),
                "w",
                encoding="utf8",
            ) as outfile:
                json.dump(self.data, outfile, indent=4)
        except:
            with open(
                os.path.join(self.datafolder, "telegram_data", fname),
                "w",
                encoding="utf8",
            ) as outfile:
                json.dump(self.data, outfile, indent=4)

    def read_config(self):
        try:
            with open(os.path.join(self.config_file), "r", encoding="utf8") as json_file:
                self.config = json.load(json_file)
        except FileNotFoundError:
            return 
        except json.decoder.JSONDecodeError:
            return 

    def write_config(self):
        try:
            with open(
                os.path.join(self.config_file),
                "w",
                encoding="utf8",
            ) as outfile:
                json.dump(self.config, outfile, indent=4)
        except:
            return

    def getAllBotList(self) -> List[str]:
        '''Return ALL contents of telegram_data folder'''
        jsonfiles = sorted(os.listdir(os.path.join(self.datafolder, "telegram_data")))

        i=len(jsonfiles)-1
        while i >= 0:
            if jsonfiles[i] == "data.json" or jsonfiles[i].__contains__("output.json") or jsonfiles[i].__contains__(".csv") or jsonfiles[i] == "settings.json":
                jsonfiles.pop(i)
            else:
                while self.read_data(jsonfiles[i]) == False:
                    sleep(0.1)
            i -= 1
        jsonfiles.sort()
        return [x.replace(".json", "") if x.__contains__(".json") else x for x in jsonfiles]

    def getActiveBotList(self, state: str = "active") -> List[str]:
        '''Return contents of telegram_data folder'''
        jsonfiles = self.getAllBotList()

        i=len(jsonfiles)-1
        while i >= 0:
            while self.read_data(jsonfiles[i]) is False:
                sleep(0.2)
            if "botcontrol" in self.data:
                if not self.data["botcontrol"]["status"] == state:
                    jsonfiles.pop(i)
            i -= 1
        jsonfiles.sort()
        return [x.replace(".json", "") if x.__contains__(".json") else x for x in jsonfiles]

    def getActiveBotListWithOpenOrders(self, state: str = "active") -> List[str]:
        '''Return contents of telegram_data folder active bots with an open order'''
        jsonfiles = self.getAllBotList()

        i=len(jsonfiles)-1
        while i >= 0:
            while self.read_data(jsonfiles[i]) == False:
                sleep(0.1)
            if "botcontrol" in self.data:
                margin_string = str(self.data["margin"]).strip()
                if not self.data["botcontrol"]["status"] == state and not margin_string == "":
                    jsonfiles.pop(i)
            i -= 1
        jsonfiles.sort()
        return [x.replace(".json", "") if x.__contains__(".json") else x for x in jsonfiles]

    def getHungBotList(self, state: str = "active") -> List[str]:
        '''Return contents of telegram_data folder - working out which are hung bots'''
        jsonfiles = self.getAllBotList()

        i=len(jsonfiles)-1
        while i >= 0:
            while self.read_data(jsonfiles[i]) == False:
                sleep(0.2)
            if "botcontrol" in self.data:
                last_ping = datetime.strptime(self.data["botcontrol"]["watchdog_ping"], "%Y-%m-%dT%H:%M:%S.%f")
                current_dt = datetime.now()
                ping_delta = int((current_dt - last_ping).total_seconds())
                if (self.data["botcontrol"]["status"] == state and ping_delta < 600):
                    jsonfiles.pop(i)
            i -= 1
        jsonfiles.sort()
        return [x.replace(".json", "") if x.__contains__(".json") else x for x in jsonfiles]

    def isBotRunning(self, pair) -> bool:
        if os.path.isfile(
                os.path.join(self.datafolder, "telegram_data", f"{pair}.json")
            ):
            return True
            
        return False

    def getRunningBotExchange(self, pair) -> str:
        if self.read_data(f"{pair}.json") == True:
            return self.data["exchange"]
        return "None"

    def startProcess(self, pair, exchange, overrides, startmethod: str = "telegram", returnOutput: bool = False):
        '''Start a new subprocess'''

        if self.isBotRunning(pair):
            return False

        if returnOutput == True:
            return subprocess.getoutput(
                f"python3 pycryptobot.py --exchange {exchange} --market {pair} {overrides}")

        command = "python3 pycryptobot.py"
        command = f"{command} --startmethod {startmethod}"

        if pair != "":
            command = f"{command} --market {pair}"
        if exchange != "":
            command = f"{command} --exchange {exchange}"

        if platform.system() == "Windows":
            os.system(
                    f"start powershell -Command $host.UI.RawUI.WindowTitle = '{pair}' ; "
                    f"{command} --logfile './logs/{exchange}-{pair}-{datetime.now().date()}.log' {overrides}"
                )
        else:
            subprocess.Popen(
                    f"{command} --logfile './logs/{exchange}-{pair}-{datetime.now().date()}.log' {overrides}",
                    shell=True,
                )

        return True

    def updatebotcontrol(self, pair, status) -> bool:
        """used to update bot json files for controlling state"""
        self.read_data(pair)

        if "botcontrol" in self.data:
            self.data["botcontrol"]["status"] = status
            self.write_data(pair)
            return True

        return False

    def stopRunningBot(self, pair, state, isOpen: bool = False):
        if self.isBotRunning(pair):
            done = False
            while done == False:
                try:
                    self.read_data(pair)
                    if isOpen:
                        self.updatebotcontrol(pair, state)
                    elif "margin" in self.data and self.data["margin"] == " ":
                        self.updatebotcontrol(pair, state)
                    done = True
                except:
                    pass

