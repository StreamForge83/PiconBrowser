from re import match, findall
from unicodedata import normalize

from enigma import eServiceCenter, eServiceReference

from Components.config import config
from Components.SystemInfo import BoxInfo
from ServiceReference import ServiceReference
from Tools.Directories import sanitizeFilename

SKIP_BOUQUET_NAMES = "userbouquet.lastscanned"
BOUQUET_FILENAME_PATTERN = r'FROM BOUQUET "([^"]+)"'


def getChannelKey(service):
	channelKeyMatch = match("([^:]+):([^:]+):([^:]+):([^:]+):([^:]+):([^:]+):([^:]+):([^:]+):([^:]+):([^:]+):", str(service))
	if channelKeyMatch:
		channelKey = "_".join(map(str, channelKeyMatch.groups()))
		try:
			return normalize("NFKD", channelKey)
		except Exception:
			return channelKey


def getCleanFileName(value):
	# utf8snp picon naming: keep UTF8 characters (only strip filesystem-unsafe ones), same as Components/Renderer/Picon.py.
	return sanitizeFilename(value.replace("\x80", "").replace("\x86", "").replace("\x87", "")).lower()


class BouquetParser:
	def __init__(self, bouquetPath):
		self.serviceList = []
		self.bouquetPath = bouquetPath
		self.excludeIptv = config.plugins.PiconBrowser.excludeIptv.value
		self.excludeRadio = config.plugins.PiconBrowser.excludeRadio.value
		self.__loadBouquetList()

	def getServiceList(self):
		return self.serviceList

	def __loadBouquetList(self):
		with open(f"{self.bouquetPath}/bouquets.tv") as file:
			data = file.read()
		bouquetFilesTV = findall(BOUQUET_FILENAME_PATTERN, data)
		self.serviceList = []
		for fileName in bouquetFilesTV:
			if SKIP_BOUQUET_NAMES not in fileName.lower():
				bouquetList = eServiceReference(f'1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "{fileName}" ORDER BY bouquet')
				self.serviceList += self.__getBouquetServices(bouquetList)
		if self.excludeRadio:
			return
		with open(f"{self.bouquetPath}/bouquets.radio") as file:
			data = file.read()
		bouquetFilesRadio = findall(BOUQUET_FILENAME_PATTERN, data)
		for fileName in bouquetFilesRadio:
			if SKIP_BOUQUET_NAMES not in fileName.lower():
				bouquetList = eServiceReference(f'1:7:2:0:0:0:0:0:0:0:FROM BOUQUET "{fileName}" ORDER BY bouquet')
				self.serviceList += self.__getBouquetServices(bouquetList)

	def __getBouquetServices(self, bouquet):
		services = []
		serviceList = eServiceCenter.getInstance().list(bouquet)
		if serviceList is not None:
			getServiceHook = BoxInfo.getItem("getServiceHook")
			while True:
				service = serviceList.getNext()
				if not service.valid():
					break
				if service.flags & (eServiceReference.isDirectory | eServiceReference.isMarker):
					continue
				if getServiceHook and callable(getServiceHook):
					_service = getServiceHook(service, self.excludeIptv)
				else:
					_service = self.getService(service)
				if _service:
					services.append(_service)
		return services

	def getService(self, service):
		if self.excludeIptv:
			sref = service.toString()
			fields = sref.split(":", 10)[:10]
			if fields[0] != "1":
				return None
			sref = f"{':'.join(fields)}:"
			return ServiceReference(sref)
		return ServiceReference(service)
