import urllib

PREFIX = '/video/s4u'
TITLE = 'S4U'
ART = 'art-default.jpg'
ICON = 'icon-default.jpg'
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6_8_13) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Safari/604.1.38'

DOMAIN = Prefs['protocol'] + '://app.seasons4u.com/'
MENU = DOMAIN + 'api/apps/v1/menu/'
WATCH = DOMAIN + 'api/apps/v1/plex/watch/'
AUTH = DOMAIN + 'token'
#Q = Prefs['quality']
token = ''
qList = {}
qList["Auto Quality"] = "9"
qList["150K"] = "8"
qList["400K"] = "7"
qList["800K"] = "6"
qList["1200K"] = "5"
qList["1600K"] = "4"
qList["2400K"] = "3"
qList["3000K"] = "2"
qList["4500K"] = "1"
qList["6000K (When Available)"] = "15"
qList["10000K (When Available)"] = "16"

####################################################################################################
def Start():
    #Log.Debug()    
    ObjectContainer.title = TITLE

    #ObjectContainer.title1 = TITLE
	#HTTP.CacheTime = CACHE_1HOUR

####################################################################################################
@handler(PREFIX, TITLE, art=ART, thumb=ICON)
def MainMenu(**kwargs):    
	getToken(True)
	oc = ObjectContainer()
	json_obj = GetJSON(MENU + "0?addonVersion=1.1.1")

	for member in json_obj:

		url = MENU + member['Id']
		title = member['Description']
		thumb = member['Image']

		oc.add(DirectoryObject(key = Callback(SubMenu, url=url, id=member['Id'], title=title),
			title = member['Description'],
			thumb = thumb))

	return oc

####################################################################################################
@route(PREFIX + '/submenu')
def SubMenu(url, id, title, **kwargs):

	oc = ObjectContainer(title2=title, no_cache=True)
	json_obj = GetJSON(url)

	for m in json_obj:

		description = m["Description"]
		url = MENU + m['Id']
		thumb = m['Image']
		if m["Type"] == 0 and m["Description"] != "*Quality Settings":                      
			oc.add(DirectoryObject(key = Callback(SubMenu, url=MENU + m['Id'], title=m['Description'], id=m['Id']),
				title = description,
				thumb = thumb))
		elif m["Type"] == 1:        
			streamurl = WATCH + m['VideoType'] + '/' + str(m['VideoId']) + '/' + getQ()
			oc.add(getStream(url=streamurl,key=streamurl,description=description,thumb=thumb))
		elif m["Type"] == 2:          
			oc.add(DirectoryObject(key = Callback(SubMenu, url=MENU + m['Id'] + '?options=' + m['Options'], title=m['Description'], id=m['Id']),
				title = description,
				thumb = thumb))
		elif m["Type"] == 3:          
			oc.add(DirectoryObject(key = Callback(SubMenu, url=MENU + m['Id'], title=m['Description'], id=m['Id']),
				title = description,
				thumb = thumb))
	return oc

####################################################################################################
@route(PREFIX + '/api/json')
def GetJSON(url, **kwargs):
	json_obj = JSON.ObjectFromURL(url, headers={"User-Agent": USER_AGENT, "Authorization": token, "Content-Length":0}, method = "POST")
	return json_obj

@indirect
def PlayStream(url, **kwargs):
	Log('s4url: %s' % (url))
	return IndirectResponse(VideoClipObject, key=HTTPLiveStreamURL(url))

def getStream(url,key,description,thumb, **kwargs):	
    m3u8Url = HTTP.Request(url,method="POST",headers={"User-Agent": USER_AGENT, "Authorization": token, "Content-Length":0}).content.replace('"','')
    
    return VideoClipObject(key = Callback(StreamMetadata, url=url, key=key, description=description, thumb=thumb),
		rating_key = key,
		title = description,
        thumb = thumb,
		items = [MediaObject(video_codec = VideoCodec.H264,
                        audio_codec = AudioCodec.AAC,
                        protocol = 'hls',
                        audio_channels = 2,
						optimized_for_streaming = True,
                        parts = [PartObject(key = HTTPLiveStreamURL(Callback(PlayStream, url=m3u8Url)))])])

def StreamMetadata(url,key,description,thumb,**kwargs):
	oc = ObjectContainer()
	oc.add(getStream(url,key,description,thumb))
	return oc

def getToken(firstLoad, **kwargs):
	auth_values = "username=%s&password=%s&grant_type=password" % (urllib.quote(Prefs['username']), urllib.quote(Prefs['password']))
	res = HTTP.Request(url=AUTH, data=auth_values, headers={"User-Agent": USER_AGENT, "Content-Type": "application/x-www-form-urlencoded", "Method":"POST"})
	json_obj = JSON.ObjectFromString(res.content)
	global token
	token = 'Bearer ' + json_obj['access_token']

def getQ(**kwargs):
	return str(qList[Prefs['quality']])